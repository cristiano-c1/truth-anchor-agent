from cdp import Cdp, Wallet
import json

# Replace these with your actual CDP API keys from the Coinbase Portal
# If you don't have these yet, go to https://cdp.coinbase.com/
Cdp.configure("YOUR_API_KEY_NAME", "YOUR_API_KEY_PRIVATE_KEY")

# Create the wallet on Base network
wallet = Wallet.create(network_id="base")

# Export the data so you can save it!
wallet_data = wallet.export_data()

# Save this to a file - THIS IS YOUR KEY!
with open("my_agent_wallet.json", "w") as f:
    json.dump(wallet_data.to_dict(), f)

print(f"NEW WALLET CREATED: {wallet.default_address.address_id}")
print("IMPORTANT: Your keys are saved in my_agent_wallet.json. Do not lose this file!")