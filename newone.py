import os
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import signal

# Токены из переменных окружения
HF_TOKEN = os.environ["HF_TOKEN"]
HF_API_URL_TEXT = "https://api-inference.huggingface.co/models/ai-forever/rugpt3medium_based_on_gpt2"


HF_API_URL_IMAGE = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
TELEGRAM_BOT_TOKEN = "7809664280:AAFxh7WtpuO8Kmplek6bMpP3bus_ctnoovs"


if not HF_TOKEN or not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Ошибка: переменные окружения HF_TOKEN или TG_BOT_TOKEN не установлены!")

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- Логика для генерации изображений с лимитами и сохранением данных ---

USER_DATA_FILE = "user_data.json"
MAX_FREE_GENERATIONS = 3

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            for user_id, info in data.items():
                info["last_reset"] = datetime.fromisoformat(info["last_reset"])
                if "premium" not in info:
                    info["premium"] = False
            return defaultdict(lambda: {"count": 0, "last_reset": datetime.now(), "premium": False}, data)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaultdict(lambda: {"count": 0, "last_reset": datetime.now(), "premium": False})

def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump({
            str(uid): {
                "count": info["count"],
                "last_reset": info["last_reset"].isoformat(),
                "premium": info.get("premium", False)
            } for uid, info in user_limits.items()
        }, f, indent=2)

def reset_if_needed(user_data):
    if datetime.now() - user_data["last_reset"] > timedelta(days=1):
        user_data["count"] = 0
        user_data["last_reset"] = datetime.now()
        save_user_data()

user_limits = load_user_data()

# --- Обработчики Telegram ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для генерации изображений и общения.\n\n"
        "Команды:\n"
        "/generate [текст] — сгенерировать изображение\n"
        "Просто напиши любое сообщение — я отвечу текстом."
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = user_limits[user_id]
    reset_if_needed(user_data)

    if not user_data.get("premium", False) and user_data["count"] >= MAX_FREE_GENERATIONS:
        await update.message.reply_text(
            "🚫 Лимит бесплатных генераций на сегодня исчерпан.\n"
            "Оформите подписку: /buy или активируйте промокод: /promo"
        )
        return

    prompt = " ".join(context.args) if context.args else "a futuristic city at sunset"
    await update.message.reply_text("Генерирую изображение... ⏳")

    response = requests.post(
        HF_API_URL_IMAGE,
        headers=HEADERS,
        json={"inputs": prompt}
    )

    if response.status_code != 200:
        await update.message.reply_text(f"Ошибка API: {response.status_code}\n{response.text}")
        return

    image_data = response.content
    user_data["count"] += 1
    save_user_data()

    await update.message.reply_photo(photo=image_data, caption="Вот твоё изображение! 🎨")

VALID_PROMOCODES = {"SUPERPREMIUM2025", "VIPACCESS"}

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = user_limits[user_id]

    if not context.args:
        await update.message.reply_text("❗️ Укажи промокод после команды.\nПример: /promo SUPERPREMIUM2025")
        return

    code = context.args[0].strip().upper()

    if code in VALID_PROMOCODES:
        if user_data.get("premium", False):
            await update.message.reply_text("✅ У тебя уже активирован премиум-статус!")
        else:
            user_data["premium"] = True
            save_user_data()
            await update.message.reply_text("🎉 Поздравляю! У тебя активирован премиум-статус — неограниченное количество генераций.")
    else:
        await update.message.reply_text("❌ Неверный промокод. Попробуй ещё раз.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 *Тарифы:*\n"
        "— Бесплатно: 3 изображения в день\n"
        "— Премиум: от 100₽/мес — больше генераций, без лимитов\n\n"
        "🛒 Оплатить можно на Boosty: https://boosty.to/твоя_ссылка\n"
        "После оплаты напиши /activate или свяжись с админом.",
        parse_mode="Markdown"
    )

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = user_limits[user_id]
    reset_if_needed(user_data)

    if user_data.get("premium", False):
        await update.message.reply_text(
            f"👤 Статус: Премиум-пользователь 💎\n"
            f"У тебя неограниченное количество генераций!"
        )
    else:
        remaining = MAX_FREE_GENERATIONS - user_data["count"]
        next_reset = user_data["last_reset"] + timedelta(days=1)
        time_left = next_reset - datetime.now()

        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes = remainder // 60

        await update.message.reply_text(
            f"👤 Статус:\n"
            f"Сегодня использовано: {user_data['count']} / {MAX_FREE_GENERATIONS}\n"
            f"Осталось: {remaining} генераций\n"
            f"⏳ До обновления: {hours} ч {minutes} мин"
        )

# --- Функция для генерации текста через ruGPT ---

def generate_response(prompt: str) -> str:
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL_TEXT, headers=HEADERS, json=payload)
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

# --- Graceful shutdown ---

def save_and_exit(*args):
    print("Сохраняю данные перед завершением...")
    save_user_data()
    exit(0)

signal.signal(signal.SIGINT, save_and_exit)
signal.signal(signal.SIGTERM, save_and_exit)

# --- Запуск бота ---

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Команды для генерации изображений
    app.add_handler(CommandHandler("generate", generate_image))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("me", me))

    # Обработка всех текстовых сообщений (кроме команд) через ruGPT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    print("🤖 Бот запущен!")
    app.run_polling()
