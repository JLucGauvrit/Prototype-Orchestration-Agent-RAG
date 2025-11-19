FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    "mcp[cli]" \
    httpx

# Le serveur MCP communique via stdio, pas besoin d'exposer de port

CMD ["python", "main.py"]
