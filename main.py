import base64
import json
import os
import secrets
import sqlite3
import time
import requests
import eth_abi
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from eth_account import Account
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from web3 import Web3
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# --- Constants ---
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_DECIMALS = 6
MIN_AMOUNT = 5000  # 0.005 USDC in smallest unit
FREE_TIER_REQUESTS = 50
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

w3 = Web3(Web3.HTTPProvider(BASE_RPC))


# --- HTML meta parser ---
class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attrs = dict(attrs)
            name = attrs.get("name", "").lower()
            prop = attrs.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.description = attrs.get("content", "")

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

# --- SQLite setup ---
DB_PATH = "/data/payments.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS used_payments "
        "(tx_hash TEXT PRIMARY KEY, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS api_keys ("
        "api_key TEXT PRIMARY KEY, "
        "agent_name TEXT DEFAULT '', "
        "agent_url TEXT DEFAULT '', "
        "free_remaining INTEGER DEFAULT 50, "
        "total_requests INTEGER DEFAULT 0, "
        "paid_requests INTEGER DEFAULT 0, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    con.commit()
    con.close()

init_db()


# --- API key management ---
def provision_key(agent_name: str = "", agent_url: str = "") -> dict:
    api_key = "ta_" + secrets.token_urlsafe(32)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO api_keys (api_key, agent_name, agent_url, free_remaining) VALUES (?, ?, ?, ?)",
        (api_key, agent_name, agent_url, FREE_TIER_REQUESTS),
    )
    con.commit()
    con.close()
    return {
        "api_key": api_key,
        "free_requests_remaining": FREE_TIER_REQUESTS,
        "message": f"Ready. First {FREE_TIER_REQUESTS} requests free. Then 0.005 USDC/request on Base.",
        "usage": "Include header: Authorization: Bearer <api_key>",
    }


def get_key_info(api_key: str) -> dict | None:
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT free_remaining, total_requests, paid_requests, agent_name FROM api_keys WHERE api_key = ?",
        (api_key,),
    ).fetchone()
    con.close()
    if not row:
        return None
    return {"free_remaining": row[0], "total_requests": row[1], "paid_requests": row[2], "agent_name": row[3]}


def use_free_request(api_key: str) -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE api_keys SET free_remaining = free_remaining - 1, total_requests = total_requests + 1 WHERE api_key = ?",
        (api_key,),
    )
    con.commit()
    con.close()


def record_paid_request(api_key: str) -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE api_keys SET total_requests = total_requests + 1, paid_requests = paid_requests + 1 WHERE api_key = ?",
        (api_key,),
    )
    con.commit()
    con.close()

# --- Payment verification ---
def verify_payment(tx_hash: str) -> bool:
    """Returns True if tx_hash is a valid, unused USDC payment to our wallet."""
    wallet = os.getenv("MY_WALLET_ADDRESS", "").lower()
    if not wallet:
        return False

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return False

    if receipt is None or receipt.get("status") != 1:
        return False

    usdc = USDC_CONTRACT.lower()
    found = False
    for log in receipt.get("logs", []):
        if log["address"].lower() != usdc:
            continue
        topics = log.get("topics", [])
        if len(topics) < 3:
            continue
        if topics[0].hex() != TRANSFER_TOPIC:
            continue
        to_addr = "0x" + topics[2].hex()[-40:]
        if to_addr.lower() != wallet:
            continue
        amount = int(log["data"].hex(), 16)
        if amount >= MIN_AMOUNT:
            found = True
            break

    if not found:
        return False

    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT 1 FROM used_payments WHERE tx_hash = ?", (tx_hash,)
    ).fetchone()
    if row:
        con.close()
        return False

    con.execute("INSERT INTO used_payments (tx_hash) VALUES (?)", (tx_hash,))
    con.commit()
    con.close()
    return True


def _eip712_hash(authorization: dict) -> bytes:
    """Compute EIP-712 hash for USDC TransferWithAuthorization on Base mainnet."""
    domain_type_hash = Web3.keccak(text=(
        "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
    ))
    transfer_type_hash = Web3.keccak(text=(
        "TransferWithAuthorization(address from,address to,uint256 value,"
        "uint256 validAfter,uint256 validBefore,bytes32 nonce)"
    ))

    domain_sep = Web3.keccak(eth_abi.encode(
        ["bytes32", "bytes32", "bytes32", "uint256", "address"],
        [
            bytes(domain_type_hash),
            bytes(Web3.keccak(text="USD Coin")),
            bytes(Web3.keccak(text="2")),
            8453,  # Base mainnet
            Web3.to_checksum_address(USDC_CONTRACT),
        ],
    ))

    nonce_hex = authorization.get("nonce", "0x" + "0" * 64)
    if isinstance(nonce_hex, str):
        nonce_hex = nonce_hex[2:] if nonce_hex.startswith("0x") else nonce_hex
    nonce_bytes = bytes.fromhex(nonce_hex.zfill(64))

    struct_hash = Web3.keccak(eth_abi.encode(
        ["bytes32", "address", "address", "uint256", "uint256", "uint256", "bytes32"],
        [
            bytes(transfer_type_hash),
            Web3.to_checksum_address(authorization["from"]),
            Web3.to_checksum_address(authorization["to"]),
            int(authorization["value"]),
            int(authorization.get("validAfter", 0)),
            int(authorization["validBefore"]),
            nonce_bytes,
        ],
    ))

    return bytes(Web3.keccak(b"\x19\x01" + bytes(domain_sep) + bytes(struct_hash)))


def verify_x402_payment(x_payment_header: str) -> tuple[bool, str]:
    """Verify x402 EIP-3009 signed authorization from X-Payment header.
    Returns (ok, error_message). Marks nonce as used on success."""
    wallet = os.getenv("MY_WALLET_ADDRESS", "").lower()
    if not wallet:
        return False, "Wallet not configured"

    try:
        payment_data = json.loads(base64.b64decode(x_payment_header))
    except Exception:
        return False, "Invalid X-Payment header encoding"

    if payment_data.get("scheme") != "exact":
        return False, "Unsupported payment scheme"
    if payment_data.get("network") not in ("base", "base-mainnet"):
        return False, "Unsupported network (use 'base')"

    payload = payment_data.get("payload", {})
    authorization = payload.get("authorization", {})
    signature = payload.get("signature", "")

    if not authorization or not signature:
        return False, "Missing authorization or signature in payload"

    if authorization.get("to", "").lower() != wallet:
        return False, f"Wrong recipient: {authorization.get('to')}"

    if int(authorization.get("value", 0)) < MIN_AMOUNT:
        return False, f"Amount too low (min {MIN_AMOUNT} = 0.005 USDC)"

    valid_before = int(authorization.get("validBefore", 0))
    if valid_before < int(time.time()):
        return False, "Authorization expired"

    nonce = authorization.get("nonce", "")
    con = sqlite3.connect(DB_PATH)
    if con.execute("SELECT 1 FROM used_payments WHERE tx_hash = ?", (nonce,)).fetchone():
        con.close()
        return False, "Authorization nonce already used"

    try:
        msg_hash = _eip712_hash(authorization)
        recovered = Account._recover_hash(msg_hash, signature=signature)
        if recovered.lower() != authorization.get("from", "").lower():
            con.close()
            return False, "Invalid signature"
    except Exception as e:
        con.close()
        return False, f"Signature verification error: {e}"

    con.execute("INSERT INTO used_payments (tx_hash) VALUES (?)", (nonce,))
    con.commit()
    con.close()
    return True, ""


def _payment_required_body(resource_url: str) -> dict:
    wallet = os.getenv("MY_WALLET_ADDRESS", "")
    return {
        "accepts": [{
            "scheme": "exact",
            "network": "base",
            "maxAmountRequired": str(MIN_AMOUNT),
            "resource": resource_url,
            "description": "URL verification - 0.005 USDC on Base",
            "mimeType": "application/json",
            "payTo": wallet,
            "maxTimeoutSeconds": 300,
            "asset": USDC_CONTRACT,
            "extra": {"name": "USDC", "version": "2"},
        }],
        "error": "X-Payment header required",
    }


# --- MCP Server ---
mcp = FastMCP("Truth Anchor Agent", host="0.0.0.0")

@mcp.tool()
def verify_url(url: str, tx_hash: str = "", claim: str = "") -> dict:
    """
    Verify if a URL is live, accessible, and optionally contains a specific claim.

    Requires a 0.005 USDC payment on Base blockchain.
    If tx_hash is empty, returns payment instructions.
    After sending USDC, call again with the transaction hash.

    Args:
        url: The URL to verify (e.g. https://example.com)
        tx_hash: Transaction hash of the 0.005 USDC payment on Base
        claim: Optional text to check for in the page content (e.g. "climate change")
    """
    wallet = os.getenv("MY_WALLET_ADDRESS", "")

    if not tx_hash:
        return {
            "payment_required": True,
            "amount": "0.005 USDC",
            "network": "base",
            "wallet_address": wallet,
            "instructions": f"Send 0.005 USDC to {wallet} on Base, then call this tool again with the transaction hash as tx_hash."
        }

    if not verify_payment(tx_hash):
        return {
            "error": "Payment not verified",
            "payment_required": True,
            "wallet_address": wallet,
        }

    try:
        r = requests.get(url, timeout=10, allow_redirects=True, verify=True)
        final_url = r.url
        redirected = final_url.rstrip("/") != url.rstrip("/")
        ssl_valid = url.startswith("https://")

        parser = MetaParser()
        parser.feed(r.text[:50000])

        result = {
            "url": url,
            "final_url": final_url,
            "is_live": 200 <= r.status_code < 400,
            "status_code": r.status_code,
            "redirected": redirected,
            "ssl_valid": ssl_valid,
            "title": parser.title.strip(),
            "description": parser.description.strip(),
            "payment_verified": True
        }

        if claim:
            result["claim_found"] = claim.lower() in r.text.lower()

        return result
    except requests.exceptions.SSLError:
        return {"url": url, "is_live": False, "ssl_valid": False, "error": "SSL certificate invalid"}
    except Exception as e:
        return {"url": url, "is_live": False, "error": str(e)}


# --- FastAPI app ---
# Initialize MCP ASGI app first so session_manager is created
_mcp_asgi = mcp.streamable_http_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield

app = FastAPI(title="Truth Anchor Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP streamable HTTP server at /mcp
app.mount("/mcp", _mcp_asgi)


@app.get("/")
async def health_check():
    """Check that the agent is online."""
    return {
        "status": "online",
        "agent": "Truth Anchor",
        "version": "1.0.0",
        "payment_network": "base",
        "mcp_endpoint": "https://truth-anchor-agent.fly.dev/mcp"
    }

@app.get("/mcp.json")
async def get_mcp_config():
    """Manifest for AI Agent Marketplaces (Model Context Protocol)."""
    return {
        "mcp_version": "2026.1",
        "name": "Truth-Anchor-Agent",
        "description": "Real-time URL verification to prevent AI hallucinations.",
        "capabilities": {
            "url_verification": {
                "pricing": "0.005 USDC",
                "network": "base",
                "address": os.getenv("MY_WALLET_ADDRESS")
            }
        },
        "endpoints": {
            "verify": "https://truth-anchor-agent.fly.dev/verify",
            "mcp": "https://truth-anchor-agent.fly.dev/mcp"
        }
    }

@app.post("/auth/provision")
async def provision(request: Request):
    """
    Get a free API key instantly. No signup, no email.
    First 50 requests are free. Then 0.005 USDC/request via x402.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    return provision_key(
        agent_name=body.get("agent_name", ""),
        agent_url=body.get("agent_url", ""),
    )


@app.get("/revenue")
async def revenue():
    """Revenue stats."""
    con = sqlite3.connect(DB_PATH)
    total_keys     = con.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    total_requests = con.execute("SELECT COALESCE(SUM(total_requests), 0) FROM api_keys").fetchone()[0]
    paid_requests  = con.execute("SELECT COALESCE(SUM(paid_requests), 0) FROM api_keys").fetchone()[0]
    con.close()
    return {
        "total_api_keys": total_keys,
        "total_requests": total_requests,
        "paid_requests": paid_requests,
        "revenue_usdc": round(paid_requests * 0.005, 6),
    }


@app.post("/verify")
async def verify_link(request: Request):
    """
    URL verification.

    Flow:
      1. GET /auth/provision → ricevi api_key (prime 50 gratis)
      2. POST /verify con header Authorization: Bearer <api_key>
      3. Dopo 50 richieste: aggiungi X-Payment (EIP-3009 firmato) per pagare 0.005 USDC
    """
    # --- Verifica API key ---
    auth_header = request.headers.get("Authorization", "")
    api_key = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""

    if not api_key:
        return Response(
            status_code=401,
            content=json.dumps({
                "error": "API key required",
                "how_to_get": "POST /auth/provision",
                "message": f"Get a free API key. First {FREE_TIER_REQUESTS} requests are free.",
            }),
            media_type="application/json",
        )

    key_info = get_key_info(api_key)
    if not key_info:
        return Response(
            status_code=401,
            content=json.dumps({"error": "Invalid API key. Get one via POST /auth/provision"}),
            media_type="application/json",
        )

    # --- Free tier o pagamento ---
    paid = False
    if key_info["free_remaining"] > 0:
        use_free_request(api_key)
    else:
        x_payment = request.headers.get("X-Payment")
        if not x_payment:
            return Response(
                status_code=402,
                content=json.dumps({
                    **_payment_required_body(str(request.url)),
                    "free_requests_remaining": 0,
                    "message": "Free tier exhausted. Payment required.",
                }),
                media_type="application/json",
            )
        ok, error = verify_x402_payment(x_payment)
        if not ok:
            return Response(
                status_code=402,
                content=json.dumps({"error": error, **_payment_required_body(str(request.url))}),
                media_type="application/json",
            )
        record_paid_request(api_key)
        paid = True

    # --- Esegui verifica ---
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            return Response(status_code=400, content='{"error":"url field required"}', media_type="application/json")

        r = requests.get(url, timeout=10, allow_redirects=True, verify=True)
        final_url = r.url
        redirected = final_url.rstrip("/") != url.rstrip("/")
        return {
            "url": url,
            "final_url": final_url,
            "is_live": 200 <= r.status_code < 400,
            "status_code": r.status_code,
            "redirected": redirected,
            "ssl_valid": url.startswith("https://"),
            "free_requests_remaining": max(0, key_info["free_remaining"] - (0 if paid else 1)),
            "paid": paid,
        }
    except requests.exceptions.SSLError:
        return {"url": url, "is_live": False, "ssl_valid": False, "error": "SSL certificate invalid"}
    except Exception as e:
        return {"url": url, "is_live": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
