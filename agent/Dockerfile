FROM python:3.13-slim

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU-only torch first)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    chromadb \
    requests \
    sentence-transformers \
    PyPDF2 \
    pandas \
    pyarrow

WORKDIR /app

# Copy Python files
COPY agent.py .
COPY vectorisation.py .
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

EXPOSE 5000

# Run the entrypoint script which vectorizes then starts the API
ENTRYPOINT ["./entrypoint.sh"]
