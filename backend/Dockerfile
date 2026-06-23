FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "\
import os; \
from sentence_transformers import SentenceTransformer; \
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2'); \
print('Modelo precargado ✓')"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
