from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import requests

HUGGINGFACE_API_TOKEN = os.environ["HF_TOKEN"]
HF_API_URL = "https://api-inference.huggingface.co/models/sberbank-ai/rugpt3small_based_on_gpt2"
TG_BOT_TOKEN = "7809664280:AAFxh7WtpuO8Kmplek6bMpP3bus_ctnoovs"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Функция генерации текста через Hugging Face API
def generate_response(prompt: str) -> str:
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            return response.json()[0]["generated_text"]
        except:
            return "⚠️ Ошибка в ответе модели."
    else:
        return f"⚠️ Ошибка API: {response.status_code}"

# Обработка сообщений Telegram
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    response = generate_response(user_input)
    await update.message.reply_text(response)

# Основной запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 Бот запущен!")
    app.run_polling()
