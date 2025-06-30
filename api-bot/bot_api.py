import os
from fastapi import FastAPI, Request
from telegram import Bot
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7600712992:AAGKYF0lCw7h7B-ROthuOKlb90QZM20MZis")
bot = Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

@app.post("/send_report")
async def send_report(request: Request):
    data = await request.json()
    telegram_id = data.get("telegram_id")
    resumen = data.get("resumen")
    if not telegram_id or not resumen:
        return {"ok": False, "error": "Faltan datos"}
    try:
        await bot.send_message(chat_id=telegram_id, text=resumen, parse_mode="HTML")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)} 