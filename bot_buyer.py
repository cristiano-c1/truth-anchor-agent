import requests

# L'URL del tuo agente su Fly.io
AGENT_URL = "https://truth-anchor-agent.fly.dev/verify"

def run_bot_buyer():
    print("🤖 [Bot Buyer]: Sto cercando di contattare l'agente Truth Anchor...")
    
    # Dati di esempio: chiediamo di verificare l'URL di Google
    payload = {"url": "https://google.com"}
    
    try:
        # L'agente prova a fare la richiesta senza token di pagamento
        response = requests.post(AGENT_URL, json=payload)
        
        # Se il server risponde 402, il protocollo x402 sta funzionando!
        if response.status_code == 402:
            print("✅ [Successo]: L'agente ha richiesto un pagamento (Status 402).")
            
            # Estraiamo i dati di pagamento dagli Header
            address = response.headers.get("X-Payment-Address")
            amount = response.headers.get("X-Payment-Amount")
            network = response.headers.get("X-Payment-Network")
            
            print(f"\n--- FATTURA RICEVUTA ---")
            print(f"📍 Invia a: {address}")
            print(f"💰 Importo: {amount} USDC")
            print(f"🌐 Rete:    {network.upper()}")
            print(f"------------------------\n")
            
            print("💡 Ora invia manualmente i fondi dal tuo Trust Wallet.")
            print("Appena la transazione è confermata, l'ora di lavoro sarà ufficialmente 'ripagata'!")
            
        else:
            print(f"⚠️ Errore: Il server ha risposto con status {response.status_code}")
            print("Controlla che il deploy su Fly.io sia andato a buon fine.")

    except Exception as e:
        print(f"❌ Errore di connessione: {e}")

if __name__ == "__main__":
    run_bot_buyer()