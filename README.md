# Truth Anchor Agent

A FastAPI microservice that verifies whether a URL is live, gated behind a real on-chain USDC payment on Base.

Built for the **x402 payment protocol** — AI agents pay per call, no subscriptions.

---

## What it does

1. Client calls `POST /verify` → receives a `402 Payment Required` with wallet address
2. Client sends **0.005 USDC** to the agent's wallet on Base
3. Client calls `POST /verify` again with the transaction hash in `X-402-Payment-Token`
4. Server verifies the payment on-chain (real USDC transfer, correct amount, replay-protected)
5. Server returns whether the URL is live

---

## Endpoints

### `GET /`
Health check.

### `GET /mcp.json`
Agent manifest for AI marketplaces (Model Context Protocol).

### `POST /verify`

**Headers:**
- `X-402-Payment-Token: 0x<tx_hash>` — Base transaction hash of the USDC payment

**Body:**
```json
{ "url": "https://example.com" }
```

**Response (success):**
```json
{
  "url": "https://example.com",
  "is_live": true,
  "status_code": 200,
  "payment_received": true
}
```

**Response (no/invalid payment):**
```
402 Payment Required
X-Payment-Address: 0x367B9193D4F9cb4877Ca58E6F3ce944d761d8009
X-Payment-Amount: 0.005
X-Payment-Network: base
```

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
cp .env.example .env   # add MY_WALLET_ADDRESS
pip install -r requirements.txt
uvicorn main:app --reload
```

## Deploying

```bash
fly deploy
```

---

## Live

`https://truth-anchor-agent.fly.dev`
