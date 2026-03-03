import os
import sqlite3
import requests
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
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# --- SQLite setup ---
DB_PATH = "/data/payments.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS used_payments "
        "(tx_hash TEXT PRIMARY KEY, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    con.commit()
    con.close()

init_db()

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


# --- MCP Server ---
mcp = FastMCP("Truth Anchor Agent")

@mcp.tool()
def verify_url(url: str, tx_hash: str = "") -> dict:
    """
    Verify if a URL is live and accessible.

    Requires a 0.005 USDC payment on Base blockchain.
    If tx_hash is empty, returns payment instructions.
    After sending USDC, call again with the transaction hash.

    Args:
        url: The URL to verify (e.g. https://example.com)
        tx_hash: Transaction hash of the 0.005 USDC payment on Base
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
        r = requests.head(url, timeout=5)
        return {
            "url": url,
            "is_live": 200 <= r.status_code < 400,
            "status_code": r.status_code,
            "payment_verified": True
        }
    except Exception as e:
        return {"is_live": False, "error": str(e)}


# --- FastAPI app ---
app = FastAPI(title="Truth Anchor Agent", lifespan=mcp.lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP streamable HTTP server at /mcp
# The inner app responds at /mcp, so full path is /mcp/mcp
app.mount("/mcp", mcp.streamable_http_app())


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

@app.post("/verify")
async def verify_link(request: Request):
    """
    Main endpoint with x402 payment protocol.
    Requires a payment of 0.005 USDC on Base.
    """
    payment_token = request.headers.get("X-402-Payment-Token")

    if not payment_token:
        return Response(
            status_code=402,
            headers={
                "X-Payment-Address": os.getenv("MY_WALLET_ADDRESS"),
                "X-Payment-Amount": "0.005",
                "X-Payment-Network": "base"
            },
            content="Payment Required: 0.005 USDC on Base"
        )

    if not verify_payment(payment_token):
        return Response(
            status_code=402,
            content='{"error": "Payment not verified"}',
            media_type="application/json"
        )

    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            return {"error": "URL missing"}, 400

        r = requests.head(url, timeout=5)
        return {
            "url": url,
            "is_live": 200 <= r.status_code < 400,
            "status_code": r.status_code,
            "payment_received": True
        }
    except Exception as e:
        return {"is_live": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
