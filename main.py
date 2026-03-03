import os
import sqlite3
import requests
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from web3 import Web3

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = FastAPI(title="Truth Anchor Agent")

# --- Constants ---
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_DECIMALS = 6
MIN_AMOUNT = 5000  # 0.005 USDC in smallest unit
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BASE_RPC = "https://mainnet.base.org"

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

    # Check for a USDC Transfer log to our wallet with sufficient amount
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
        # topics[2] is the 'to' address (padded to 32 bytes)
        to_addr = "0x" + topics[2].hex()[-40:]
        if to_addr.lower() != wallet:
            continue
        amount = int(log["data"].hex(), 16)
        if amount >= MIN_AMOUNT:
            found = True
            break

    if not found:
        return False

    # Replay prevention
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


@app.get("/")
async def health_check():
    """Verifica che l'agente sia online."""
    return {
        "status": "online",
        "agent": "Truth Anchor",
        "version": "1.0.0",
        "payment_network": "base"
    }

@app.get("/mcp.json")
async def get_mcp_config():
    """Manifesto per i Marketplace di Agenti AI (Model Context Protocol)."""
    return {
        "mcp_version": "2026.1",
        "name": "Truth-Anchor-Agent",
        "description": "Verifica in tempo reale se un URL è attivo per prevenire allucinazioni nelle AI.",
        "capabilities": {
            "url_verification": {
                "pricing": "0.005 USDC",
                "network": "base",
                "address": os.getenv("MY_WALLET_ADDRESS")
            }
        },
        "endpoints": {
            "verify": "https://truth-anchor-agent.fly.dev/verify"
        }
    }

@app.post("/verify")
async def verify_link(request: Request):
    """
    Endpoint principale con protocollo x402.
    Richiede un pagamento di 0.005 USDC su rete Base.
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

    # Logica di business: eseguita solo dopo il pagamento verificato on-chain
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
