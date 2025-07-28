import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

HUGGINGFACE_API_TOKEN = os.environ["HF_TOKEN"]
TELEGRAM_BOT_TOKEN = "7809664280:AAFxh7WtpuO8Kmplek6bMpP3bus_ctnoovs"

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Генерирую изображение... ⏳")

    prompt = " ".join(context.args) or "a futuristic city at sunset"

    response = requests.post(
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        headers={"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"},
        json={"inputs": prompt}
    )

    if response.status_code != 200:
        await update.message.reply_text(f"Ошибка API: {response.status_code}\n{response.text}")
        return

    image_data = response.content
    await update.message.reply_photo(photo=image_data, caption="Вот твоё изображение!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /generate [описание], чтобы получить изображение.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_image))

    print("Бот запущен...")
    app.run_polling()
