FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y procps \
    && rm -rf /var/lib/apt/lists/*
# Copiar la imagen al contenedor
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app
ENV RESIZE_IMAGES=false
CMD ["python", "app/bot.py"]
