FROM python:3.13-slim

# Installer dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    pip install --no-cache-dir fastapi uvicorn httpx && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py .

# Lancement du serveur FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
