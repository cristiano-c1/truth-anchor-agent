FROM python:3.12-slim

# Imposta la cartella di lavoro
WORKDIR /app

# Copia prima solo i requisiti (per sfruttare la cache di Docker)
COPY requirements.txt .

# Installa le librerie
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice (main.py, ecc.)
COPY . .

# Avvia il server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]