import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import requests

HF_TOKEN = os.environ["HF_TOKEN"]  # получаем токен Hugging Face из Railway environment
HF_API_URL = "https://api-inference.huggingface.co/models/sberbank-ai/rugpt3small_based_on_gpt2"
TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]  # лучше тоже хранить Telegram токен в переменных окружения

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_response(prompt: str) -> str:
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            return response.json()[0]["generated_text"]
        except Exception:
            return "⚠️ Ошибка в ответе модели."
    else:
        return f"⚠️ Ошибка API: {response.status_code}"

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    response = generate_response(user_input)
    await update.message.reply_text(response)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 Бот запущен!")
    app.run_polling()
