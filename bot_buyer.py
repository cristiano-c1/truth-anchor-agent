import requests

AGENT_URL = "https://truth-anchor-agent.fly.dev/verify"
AUTH_URL = "https://truth-anchor-agent.fly.dev/auth/provision"

def run_bot_buyer():
    print("🤖 [Bot Buyer]: Contacting Truth Anchor agent...")

    payload = {"url": "https://google.com"}

    try:
        auth_response = requests.post(
            AUTH_URL,
            json={"agent_name": "bot-buyer", "agent_url": "https://example.com/bot-buyer"},
            timeout=10,
        )
        auth_response.raise_for_status()
        api_key = auth_response.json()["api_key"]

        response = requests.post(
            AGENT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ [Success]: Source attestation completed.")
            print(response.json())
        elif response.status_code == 402:
            print("✅ [Success]: Agent requested payment (Status 402).")

            body = response.json()
            payment_terms = body.get("accepts", [{}])[0]
            address = payment_terms.get("payTo")
            amount = payment_terms.get("maxAmountRequired")
            network = payment_terms.get("network", "")

            print(f"\n--- INVOICE RECEIVED ---")
            print(f"📍 Send to: {address}")
            print(f"💰 Amount:  {amount} base units of USDC")
            print(f"🌐 Network: {network.upper()}")
            print(f"------------------------\n")

            print("💡 Send the funds manually from your wallet.")
            print("Then retry with the signed X-Payment payload once the free tier is exhausted.")

        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            print("Check that the Fly.io deploy is healthy.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    run_bot_buyer()
