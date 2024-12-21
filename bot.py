# -*- coding: utf-8 -*-

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Импорт моделей из models.py
from models import Client, DailySlot, Booking, User, Role

# Импорт Flask-приложения и базы данных
from app import app, db

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TELEGRAM_TOKEN = '1746549982:AAHS5bqktfIvJriEpHwKg8RpG4ij2sLumuA'

# Проверка токена не требуется

# Состояния для ConversationHandler
NAME, PHONE, CONFIRM, SELECT_DATE, CONFIRM_BOOKING = range(5)

def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    
    # Проверяем, зарегистрирован ли пользователь
    with app.app_context():
        client = Client.query.filter_by(telegram_id=str(user.id)).first()
        
        if client:
            update.message.reply_text(
                f'Привет, {client.name}! Вы уже зарегистрированы. '
                'Используйте /schedule для просмотра доступных дней.'
            )
            return ConversationHandler.END
        
        update.message.reply_text(
            'Привет! Давайте зарегистрируем вас в нашем бассейне. '
            'Пожалуйста, введите ваше полное имя:'
        )
        return NAME

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text(
        'Спасибо! Теперь введите ваш номер телефона:'
    )
    return PHONE

def get_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    context.user_data['phone'] = phone
    
    # Подтверждение регистрации
    reply_keyboard = [['Да', 'Нет']]
    update.message.reply_text(
        f"Подтвердите данные:\n"
        f"Имя: {context.user_data['name']}\n"
        f"Телефон: {phone}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CONFIRM

def confirm_registration(update: Update, context: CallbackContext) -> int:
    if update.message.text == 'Да':
        try:
            with app.app_context():
                logger.info(f"Регистрация нового клиента: {context.user_data}")
                
                # Проверка существования клиента с таким telegram_id
                existing_client = Client.query.filter_by(telegram_id=str(update.effective_user.id)).first()
                if existing_client:
                    logger.warning(f"Клиент с telegram_id {update.effective_user.id} уже существует")
                    update.message.reply_text('Вы уже зарегистрированы в системе.')
                    return ConversationHandler.END
                
                new_client = Client(
                    name=context.user_data['name'],
                    phone=context.user_data['phone'],
                    telegram_id=str(update.effective_user.id),
                    subscription_balance=10  # Начальный баланс
                )
                db.session.add(new_client)
                db.session.commit()
                logger.info(f"Клиент {new_client.name} успешно зарегистрирован")
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}", exc_info=True)
            update.message.reply_text('Произошла ошибка при регистрации. Попробуйте позже.')
            return ConversationHandler.END
        
        update.message.reply_text(
            'Регистрация завершена! Вам начислено 10 посещений. '
            'Используйте /schedule для бронирования.',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        update.message.reply_text(
            'Регистрация отменена. Начните заново с /start.',
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

def schedule(update: Update, context: CallbackContext):
    get_available_dates(update, context)
    return SELECT_DATE

def get_available_dates(update: Update, context: CallbackContext):
    with app.app_context():
        # Получаем доступные даты
        today = datetime.now().date()
        available_dates = DailySlot.query.filter(
            DailySlot.date >= today, 
            DailySlot.status == 'Открыт',
            DailySlot.available_slots > 0
        ).order_by(DailySlot.date).all()
        
        if not available_dates:
            update.message.reply_text('К сожалению, нет доступных дат для бронирования.')
            return ConversationHandler.END
        
        # Создаем инлайн-клавиатуру с датами
        keyboard = []
        for slot in available_dates:
            date_str = slot.date.strftime('%d.%m.%Y')
            keyboard.append([InlineKeyboardButton(
                f"{date_str} (Мест: {slot.available_slots})", 
                callback_data=f"select_date_{slot.date}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите дату:', reply_markup=reply_markup)
        return SELECT_DATE

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data.startswith('select_date_'):
        selected_date_str = data.split('_')[-1]
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        
        with app.app_context():
            slot = DailySlot.query.filter_by(date=selected_date).first()
            
            # Проверяем статус слота
            if slot.status != 'Открыт' or slot.available_slots <= 0:
                reason_text = f"\n\nПричина: {slot.reason}" if slot.reason else ""
                query.edit_message_text(f'Извините, выбранная дата больше недоступна.{reason_text}')
                return ConversationHandler.END
            
            context.user_data['selected_date'] = selected_date
            
            # Создаем инлайн-клавиатуру для подтверждения
            keyboard = [
                [InlineKeyboardButton("Подтвердить бронирование", callback_data="confirm_booking")],
                [InlineKeyboardButton("Отменить", callback_data="cancel_booking")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                f'Вы выбрали дату: {selected_date.strftime("%d.%m.%Y")}\n'
                f'Доступно мест: {slot.available_slots}\n'
                'Подтвердите бронирование:',
                reply_markup=reply_markup
            )
            return CONFIRM_BOOKING
    
    elif data == 'confirm_booking':
        confirm_booking(update, context)
    
    elif data == 'cancel_booking':
        cancel_booking(update, context)

def confirm_booking(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    selected_date = context.user_data.get('selected_date')
    
    if not selected_date:
        query.edit_message_text('Ошибка: дата не выбрана.')
        return
    
    with app.app_context():
        client = Client.query.filter_by(telegram_id=str(user.id)).first()
        slot = DailySlot.query.filter_by(date=selected_date).first()
        
        print(f"Клиент: {client}, Слот: {slot}")
        
        if not client:
            query.edit_message_text('Клиент не найден. Зарегистрируйтесь через /start')
            return
        
        if not slot:
            query.edit_message_text('Слот не найден.')
            return
        
        if slot.available_slots <= 0:
            query.edit_message_text('Нет доступных мест.')
            return
        
        # Создаем бронирование
        new_booking = Booking(
            client_id=client.id,
            daily_slot_id=slot.id,
            status='Забронировано'
        )
        
        # Уменьшаем количество доступных слотов
        slot.available_slots -= 1
        client.subscription_balance -= 1
        
        db.session.add(new_booking)
        db.session.commit()
        
        query.edit_message_text(
            f'Бронирование на {selected_date.strftime("%d.%m.%Y")} подтверждено! '
            f'Осталось посещений: {client.subscription_balance}'
        )

def cancel_booking(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text('Бронирование отменено.')
    context.user_data.pop('selected_date', None)

def book_slot(update: Update, context: CallbackContext):
    user = update.effective_user
    
    with app.app_context():
        # Проверяем клиента
        client = Client.query.filter_by(telegram_id=str(user.id)).first()
        if not client:
            update.message.reply_text('Сначала зарегистрируйтесь через /start')
            return
        
        # Проверяем баланс
        if client.subscription_balance <= 0:
            update.message.reply_text('Недостаточно посещений. Пополните абонемент.')
            return
        
        # Парсим дату из команды
        try:
            date_str = context.args[0]
            booking_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        except (IndexError, ValueError):
            update.message.reply_text('Укажите дату в формате ДД.ММ.ГГГГ')
            return
        
        # Проверяем наличие слота
        slot = DailySlot.query.filter_by(date=booking_date).first()
        if not slot or slot.available_slots <= 0:
            update.message.reply_text('На выбранную дату нет свободных мест.')
            return
        
        # Создаем бронирование
        booking = Booking(
            client_id=client.id,
            daily_slot_id=slot.id,
            status='pending'
        )
        
        slot.available_slots -= 1
        db.session.add(booking)
        db.session.commit()
        
        update.message.reply_text(
            f'Бронирование на {date_str} создано. '
            'Ожидайте подтверждения администратора.'
        )

def balance(update: Update, context: CallbackContext):
    user = update.effective_user
    
    with app.app_context():
        client = Client.query.filter_by(telegram_id=str(user.id)).first()
        if not client:
            update.message.reply_text('Сначала зарегистрируйтесь через /start')
            return
        
        update.message.reply_text(f'Ваш баланс: {client.subscription_balance} посещений')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # ConversationHandler для регистрации
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            CONFIRM: [MessageHandler(Filters.regex('^(Да|Нет)$'), confirm_registration)]
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)]
    )

    dp.add_handler(reg_handler)
    dp.add_handler(CommandHandler('schedule', schedule))
    dp.add_handler(CommandHandler('book', book_slot))
    dp.add_handler(CommandHandler('balance', balance))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(CallbackQueryHandler(confirm_booking, pattern='^confirm_booking$'))
    dp.add_handler(CallbackQueryHandler(cancel_booking, pattern='^cancel_booking$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
