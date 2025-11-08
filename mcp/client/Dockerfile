FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn requests

EXPOSE 7100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7100"]
