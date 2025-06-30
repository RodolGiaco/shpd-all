FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot_api.py ./

EXPOSE 8000

CMD ["uvicorn", "bot_api:app", "--host", "0.0.0.0", "--port", "8000"]

# Si quieres lanzar el bot y la API juntos, usa supervisord o un script bash.