from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import requests
import json

# Токен твоего Telegram бота
TELEGRAM_TOKEN = '7809664280:AAFxh7WtpuO8Kmplek6bMpP3bus_ctnoovs'

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я подключён к GigaChat.")

async def handle_message(update: Update, context):
    # Пошли сообщение от пользователя ко мне (API)
    response = requests.post(
        'https://gigachat-core.sber.ru/api/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer YOUR_GIGACHAT_API_KEY',  # сюда вставь ключ API GigaChat
        },
        data=json.dumps({
            'model': 'general',
            'messages': [
                {'role': 'system', 'content': 'Ты работаешь внутри Telegram бота.'},
                {'role': 'user', 'content': update.message.text}
            ]
        })
    )
    
    if response.status_code != 200:
        return await update.message.reply_text('Что-то пошло не так.')
        
    reply_content = response.json()['choices'][0]['message']['content']
    await update.message.reply_text(reply_content)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot is running...")
    application.run_polling()