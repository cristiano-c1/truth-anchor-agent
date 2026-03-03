# ⚓️ Truth Anchor Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built on Base](https://img.shields.io/badge/Base-Mainnet-0052FF)](https://base.org)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green)](https://modelcontextprotocol.io)
[![x402](https://img.shields.io/badge/Payment-x402-blueviolet)](https://x402.org)

**Truth Anchor Agent** is an MCP (Model Context Protocol) server that provides a verifiable grounding layer for AI agents. It verifies URL status and content accessibility, gated by **on-chain USDC micro-payments** on Base via the **x402 protocol**.

> **The Problem:** AI agents often reference dead links or hallucinate sources.
> **The Solution:** A trustless, pay-per-verification service that requires agents to commit a micro-payment before confirming a source's validity.

---

## 🛠 Model Context Protocol (MCP) Integration

This server exposes a `verify` tool that any MCP-compliant LLM (Claude Desktop, ChatGPT, IDEs) can use autonomously.

### Registration in Claude Desktop
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "truth-anchor": {
      "command": "npx",
      "args": ["-y", "truth-anchor-agent"],
      "env": {
        "MY_WALLET_ADDRESS": "0x367B9193D4F9cb4877Ca58E6F3ce944d761d8009"
      }
    }
  }
}
```

---

## 💳 The x402 Flow

The agent implements the HTTP 402 Payment Required standard, enabling seamless AI-to-AI economic transactions.

1. **Request:** Agent calls `/verify` with a URL.
2. **Challenge:** Server returns `402 Payment Required` with payment instructions.
3. **Payment:** Agent executes a 0.005 USDC transfer on Base Mainnet.
4. **Verification:** Agent retries with the transaction hash in the `X-402-Payment-Token` header.
5. **Truth:** Server validates the hash on-chain (preventing replays) and returns the status.

---

## ⚡️ API Reference

### `POST /verify`
Verifies a URL's status. Requires a valid Base transaction hash.

**Headers:**
| Header | Description |
| :--- | :--- |
| `X-402-Payment-Token` | The transaction hash of the 0.005 USDC payment on Base |

**Request Body:**
```json
{ "url": "https://base.org" }
```

**Success Response (`200 OK`):**
```json
{
  "url": "https://base.org",
  "is_live": true,
  "status_code": 200,
  "payment_verified": true
}
```

---

## 🏗 Tech Stack

- **FastAPI** — High-performance Python API framework.
- **Web3.py** — Real-time on-chain verification (Base RPC).
- **SQLite** — Replay attack prevention and transaction indexing.
- **Fly.io** — Global edge deployment.
- **Base** — L2 Ethereum for fast, low-cost USDC payments.

---

## 🛠 Local Development

```bash
# 1. Clone and Install
git clone https://github.com/cristiano-c1/truth-anchor-agent
cd truth-anchor-agent
pip install -r requirements.txt

# 2. Configure
echo "MY_WALLET_ADDRESS=0x367B9193D4F9cb4877Ca58E6F3ce944d761d8009" > .env

# 3. Run
uvicorn main:app --reload
```

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
