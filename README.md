# Truth Anchor Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built on Base](https://img.shields.io/badge/Base-Mainnet-0052FF)](https://base.org)
[![x402](https://img.shields.io/badge/Payment-x402-blueviolet)](https://x402.org)

A FastAPI microservice that verifies whether a URL is live, gated behind a real on-chain USDC payment on Base.

Built for the **x402 payment protocol** — AI agents pay per call, no subscriptions, no API keys.

**Live:** `https://truth-anchor-agent.fly.dev`

---

## How it works

```
Client                        Truth Anchor Agent              Base blockchain
  |                                   |                              |
  |-- POST /verify ------------------>|                              |
  |<-- 402 + wallet address ----------|                              |
  |                                   |                              |
  |-- send 0.005 USDC ---------------------------------->------------|
  |<-- tx hash ---------------------------------------------------- |
  |                                   |                              |
  |-- POST /verify + tx hash -------->|                              |
  |                          verify payment on-chain --------------->|
  |<-- { is_live: true } -------------|                              |
```

1. Client calls `POST /verify` → receives `402` with payment instructions
2. Client sends **0.005 USDC** to the agent's wallet on Base
3. Client calls `POST /verify` again with the transaction hash in `X-402-Payment-Token`
4. Server verifies the USDC transfer on-chain (correct amount, correct recipient, replay-protected)
5. Server returns whether the URL is live

---

## API

### `POST /verify`

**Headers:**
```
X-402-Payment-Token: 0x<tx_hash>
Content-Type: application/json
```

**Body:**
```json
{ "url": "https://example.com" }
```

**Response — success `200`:**
```json
{
  "url": "https://example.com",
  "is_live": true,
  "status_code": 200,
  "payment_received": true
}
```

**Response — no/invalid payment `402`:**
```
HTTP/1.1 402 Payment Required
X-Payment-Address: 0x367B9193D4F9cb4877Ca58E6F3ce944d761d8009
X-Payment-Amount: 0.005
X-Payment-Network: base
```

### `GET /mcp.json`
Agent manifest for AI marketplaces (Model Context Protocol).

### `GET /`
Health check.

---

## Payment details

| Field | Value |
|-------|-------|
| Network | Base (mainnet) |
| Token | USDC |
| Amount | 0.005 USDC |
| Wallet | `0x367B9193D4F9cb4877Ca58E6F3ce944d761d8009` |
| USDC contract | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

Payments are verified on-chain and stored in SQLite to prevent replay attacks.

---

## Tech stack

- **FastAPI** — API framework
- **web3.py** — Base RPC calls for on-chain verification
- **SQLite** — Replay attack prevention
- **Fly.io** — Deployment
- **Base** — L2 for cheap, fast USDC payments

---

## Running locally

```bash
# 1. Clone and install
git clone https://github.com/cristiano-c1/truth-anchor-agent
cd truth-anchor-agent
pip install -r requirements.txt

# 2. Configure
echo "MY_WALLET_ADDRESS=0xYourWalletAddress" > .env

# 3. Run
uvicorn main:app --reload
# → http://localhost:8000
```

## Deploying to Fly.io

```bash
fly launch
fly secrets set MY_WALLET_ADDRESS=0xYourWalletAddress
fly deploy
```

---

## License

MIT
