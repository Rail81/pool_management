from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sqlite3
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in .env file")

def get_db():
    return sqlite3.connect('pool.db', detect_types=sqlite3.PARSE_DECLTYPES)

def start(update, context):
    user = update.effective_user
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM client WHERE telegram_id = ?', (str(user.id),))
    client = cursor.fetchone()
    
    if not client:
        update.message.reply_text(
            'Добро пожаловать! Для регистрации, пожалуйста, отправьте свое имя и номер телефона в формате:\n'
            'Регистрация Иван Иванов, +79001234567'
        )
    else:
        update.message.reply_text(
            f'Добро пожаловать, {client[1]}!\n'
            'Используйте /schedule для просмотра доступных дней для записи\n'
            'Используйте /balance для проверки баланса абонемента'
        )
    conn.close()

def register(update, context):
    text = update.message.text
    if not text.startswith('Регистрация '):
        return
    
    try:
        _, info = text.split('Регистрация ')
        name, phone = info.split(', ')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO client (name, phone, telegram_id, subscription_balance) VALUES (?, ?, ?, ?)',
            (name, phone, str(update.effective_user.id), 0)
        )
        conn.commit()
        conn.close()
        
        update.message.reply_text(
            'Регистрация успешна!\n'
            'Используйте /schedule для просмотра доступных дней для записи\n'
            'Используйте /balance для проверки баланса абонемента'
        )
    except Exception as e:
        logger.error(f"Error in register: {e}")
        update.message.reply_text(
            'Ошибка при регистрации. Пожалуйста, используйте формат:\n'
            'Регистрация Иван Иванов, +79001234567'
        )

def schedule(update, context):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM client WHERE telegram_id = ?', (str(update.effective_user.id),))
    client = cursor.fetchone()
    
    if not client:
        update.message.reply_text('Пожалуйста, сначала зарегистрируйтесь')
        conn.close()
        return
    
    cursor.execute(
        'SELECT * FROM daily_slots WHERE date >= date("now") AND available_slots > 0'
    )
    available_days = cursor.fetchall()
    
    if not available_days:
        update.message.reply_text('К сожалению, нет доступных мест на ближайшие дни')
        conn.close()
        return
    
    keyboard = []
    for day in available_days:
        keyboard.append([InlineKeyboardButton(
            f"{day[1]} (свободно мест: {day[3]})",
            callback_data=f"book_{day[0]}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите день для записи:', reply_markup=reply_markup)
    conn.close()

def book_slot(update, context):
    query = update.callback_query
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM client WHERE telegram_id = ?', (str(query.from_user.id),))
    client = cursor.fetchone()
    
    if not client or client[4] <= 0:
        query.answer('У вас недостаточно средств на абонементе')
        conn.close()
        return
    
    slot_id = int(query.data.split('_')[1])
    cursor.execute('SELECT * FROM daily_slots WHERE id = ?', (slot_id,))
    slot = cursor.fetchone()
    
    if not slot or slot[3] <= 0:
        query.answer('Это место уже занято')
        conn.close()
        return
    
    try:
        cursor.execute(
            'UPDATE daily_slots SET available_slots = available_slots - 1 WHERE id = ?',
            (slot_id,)
        )
        cursor.execute(
            'UPDATE client SET subscription_balance = subscription_balance - 1 WHERE id = ?',
            (client[0],)
        )
        
        # Преобразуем строку даты в объект datetime
        visit_date = datetime.strptime(slot[1], '%Y-%m-%d')
        cursor.execute(
            'INSERT INTO visit (client_id, visit_date) VALUES (?, ?)',
            (client[0], visit_date)
        )
        
        conn.commit()
        conn.close()
        
        query.answer('Вы успешно записались!')
        query.edit_message_text(f'Вы записаны на {slot[1]}')
    except Exception as e:
        logger.error(f"Error in book_slot: {e}")
        query.answer('Произошла ошибка при бронировании')
        conn.rollback()
        conn.close()

def balance(update, context):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM client WHERE telegram_id = ?', (str(update.effective_user.id),))
    client = cursor.fetchone()
    
    if not client:
        update.message.reply_text('Пожалуйста, сначала зарегистрируйтесь')
    else:
        update.message.reply_text(f'Ваш текущий баланс абонемента: {client[4]} посещений')
    
    conn.close()

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("schedule", schedule))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(MessageHandler(Filters.regex('^Регистрация '), register))
    dp.add_handler(CallbackQueryHandler(book_slot, pattern='^book_'))

    # Start the bot
    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error in main: {e}")
