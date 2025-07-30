import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загрузка токенов из .env
load_dotenv()
HUGGINGFACE_API_TOKEN = os.getenv("HF_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("7809664280:AAFxh7WtpuO8Kmplek6bMpP3bus_ctnoovs")

# Ограничения генераций
MAX_FREE_GENERATIONS = 3
user_limits = defaultdict(lambda: {"count": 0, "last_reset": datetime.now()})

def reset_if_needed(user_data):
    if datetime.now() - user_data["last_reset"] > timedelta(days=1):
        user_data["count"] = 0
        user_data["last_reset"] = datetime.now()

# Команда генерации изображения
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_limits[user_id]
    reset_if_needed(user_data)

    if user_data["count"] >= MAX_FREE_GENERATIONS:
        await update.message.reply_text(
            "🚫 Вы использовали лимит бесплатных генераций на сегодня.\n"
            "Оформите подписку: /buy"
        )
        return

    prompt = " ".join(context.args) or "a futuristic city at sunset"
    await update.message.reply_text("Генерирую изображение... ⏳")

    print(f"[{datetime.now()}] User {user_id} prompt: {prompt}")

    response = requests.post(
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        headers={"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"},
        json={"inputs": prompt}
    )

    if response.status_code != 200:
        await update.message.reply_text(f"Ошибка API: {response.status_code}\n{response.text}")
        return

    image_data = response.content
    user_data["count"] += 1

    await update.message.reply_photo(photo=image_data, caption="Вот твоё изображение! 🎨")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — бот для генерации изображений по описанию.\n\n"
        "Напиши команду:\n"
        "`/generate [твой запрос]`\n\n"
        "Пример: `/generate кот в очках в космосе`\n\n"
        "🆓 Бесплатно: 3 генерации в день\n"
        "💎 Хочешь больше? Команда /buy\n"
        "📊 Статус: /me",
        parse_mode="Markdown"
    )

# Команда /buy
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 *Тарифы:*\n"
        "— Бесплатно: 3 изображения в день\n"
        "— Премиум: от 100₽/мес — больше генераций, без лимитов\n\n"
        "🛒 Оплатить можно на Boosty: https://boosty.to/твоя_ссылка\n"
        "После оплаты напиши /activate или свяжись с админом.",
        parse_mode="Markdown"
    )

# Команда /me
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_limits[user_id]
    reset_if_needed(user_data)

    remaining = MAX_FREE_GENERATIONS - user_data["count"]
    await update.message.reply_text(
        f"👤 Статус:\n"
        f"Сегодня использовано: {user_data['count']} / {MAX_FREE_GENERATIONS}\n"
        f"Осталось: {remaining} генераций"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_image))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("me", me))

    print("Бот запущен...")
    app.run_polling()
