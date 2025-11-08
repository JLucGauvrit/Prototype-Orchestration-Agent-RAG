FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn

EXPOSE 7000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]
