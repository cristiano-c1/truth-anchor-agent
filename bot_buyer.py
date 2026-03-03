import requests

AGENT_URL = "https://truth-anchor-agent.fly.dev/verify"

def run_bot_buyer():
    print("🤖 [Bot Buyer]: Contacting Truth Anchor agent...")

    payload = {"url": "https://google.com"}

    try:
        response = requests.post(AGENT_URL, json=payload)

        if response.status_code == 402:
            print("✅ [Success]: Agent requested payment (Status 402).")

            address = response.headers.get("X-Payment-Address")
            amount = response.headers.get("X-Payment-Amount")
            network = response.headers.get("X-Payment-Network")

            print(f"\n--- INVOICE RECEIVED ---")
            print(f"📍 Send to: {address}")
            print(f"💰 Amount:  {amount} USDC")
            print(f"🌐 Network: {network.upper()}")
            print(f"------------------------\n")

            print("💡 Send the funds manually from your wallet.")
            print("Once the transaction is confirmed, pass the tx hash as X-402-Payment-Token.")

        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            print("Check that the Fly.io deploy is healthy.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    run_bot_buyer()
