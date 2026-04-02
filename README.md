# ⚓️ Truth Anchor Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built on Base](https://img.shields.io/badge/Base-Mainnet-0052FF)](https://base.org)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green)](https://modelcontextprotocol.io)
[![x402](https://img.shields.io/badge/Payment-x402-blueviolet)](https://x402.org)

**Truth Anchor Agent** is an MCP (Model Context Protocol) server for **citation attestation**. Before an agent cites a source, it can verify that the URL resolves, record the final destination, capture lightweight page metadata, and return a content hash of what was fetched.

> **The Problem:** AI agents often cite dead, redirected, or changed URLs without checking what the source looked like at the time of use.
> **The Solution:** A paid verification step that records source availability and lightweight attestation metadata before the agent relies on a citation.

<a href="https://glama.ai/mcp/servers/cristiano-c1/truth-anchor-agent">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/cristiano-c1/truth-anchor-agent/badge" alt="truth-anchor-agent MCP server" />
</a>

---

## What It Guarantees

- The URL was fetched at verification time.
- The service reports the final URL, HTTP status, redirect behavior, and basic HTML metadata.
- The response includes a `content_sha256` hash so downstream systems can anchor what was observed.
- Optional claim matching is a simple substring check.

## What It Does Not Guarantee

- It is **not** a semantic fact-checking engine.
- It does **not** prove a page is trustworthy, only what the service observed when it fetched it.
- It does **not** replace search, RAG, or human review for complex claims.

---

## 🛠 Model Context Protocol (MCP) Integration

This server exposes a `verify_url` tool that any MCP-compliant LLM (Claude Desktop, ChatGPT, IDEs) can use autonomously.

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

## Interfaces

### MCP tool

The MCP tool uses a two-step flow:

1. Call `verify_url` with a URL.
2. Receive payment instructions if no payment proof is provided.
3. Retry with `tx_hash` after sending the payment.

### HTTP API

The HTTP API uses an API key plus x402-style signed payments:

1. `POST /auth/provision` to get a free API key.
2. Use the first 50 requests for free.
3. After that, attach `X-Payment` to `POST /verify`.

---

## 💳 The Payment Flow

The HTTP API implements a `402 Payment Required` flow for paid requests after the free tier is exhausted.

1. **Request:** Agent calls `/verify` with a URL.
2. **Challenge:** Server returns `402 Payment Required` with payment instructions.
3. **Payment:** Agent signs a Base USDC payment authorization.
4. **Verification:** Agent retries with the `X-Payment` header.
5. **Attestation:** Server verifies the payment and returns the source check.

---

## ⚡️ API Reference

### `POST /verify`
Verifies that a source resolves and returns attestation metadata. Requires:

- `Authorization: Bearer <api_key>`
- `X-Payment` after the free tier is exhausted

**Headers:**
| Header | Description |
| :--- | :--- |
| `Authorization` | API key returned by `POST /auth/provision` |
| `X-Payment` | Signed x402/EIP-3009 payment payload after the free tier |

**Request Body:**
```json
{
  "url": "https://base.org",
  "claim": "Base is an Ethereum L2"
}
```

**Success Response (`200 OK`):**
```json
{
  "url": "https://base.org",
  "final_url": "https://base.org/",
  "is_live": true,
  "status_code": 200,
  "redirected": false,
  "ssl_valid": true,
  "checked_at": "2026-04-02T12:00:00Z",
  "content_type": "text/html",
  "content_length_bytes": 31245,
  "title": "Base",
  "description": "Base is a secure, low-cost, builder-friendly Ethereum L2.",
  "content_sha256": "9d72c4...",
  "claim": "Base is an Ethereum L2",
  "claim_found": true,
  "claim_match_method": "substring",
  "paid": false,
  "free_requests_remaining": 49
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

## Positioning Notes

- Primary wedge: `citation attestation for agents`
- Rejected for now: broad `truth layer`, general fact-checking, and multi-tool expansion
- Product gap and validation notes live in `docs/product-positioning.md`, `docs/user-validation.md`, and `docs/user-validation-proxy.md`

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