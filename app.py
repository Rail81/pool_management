# -*- coding: utf-8 -*-

import logging
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# Импорт моделей
from models import User, Role, Client, DailySlot, Booking, Visit, SubscriptionLog, db

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_debug.log', encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)

# Создание приложения и настройка конфигурации
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pool.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEFAULT_CHARSET'] = 'utf-8'

# Инициализация базы данных
db.init_app(app)

# Инициализация базы данных при первом запуске
def init_db():
    with app.app_context():
        # Удаляем существующие данные
        db.session.query(User).delete()
        db.session.query(Role).delete()
        db.session.query(DailySlot).delete()
        
        # Создаем роли
        roles = [
            Role(
                name='Администратор', 
                description='Полный доступ ко всем функциям',
                can_manage_users=True,
                can_manage_slots=True,
                can_confirm_visits=True
            ),
            Role(
                name='Менеджер', 
                description='Управление бронированиями и посещениями',
                can_manage_users=False,
                can_manage_slots=False,
                can_confirm_visits=True
            ),
            Role(
                name='Сотрудник', 
                description='Ограниченный доступ',
                can_manage_users=False,
                can_manage_slots=False,
                can_confirm_visits=False
            )
        ]
        
        db.session.add_all(roles)
        db.session.flush()  # Получаем ID ролей
        
        # Создаем пользователей
        admin_user = User(
            username='admin', 
            email='admin@pool.com', 
            full_name='Главный Администратор',
            role=roles[0],
            is_active=True
        )
        admin_user.set_password('123')
        
        manager_user = User(
            username='manager', 
            email='manager@pool.com', 
            full_name='Менеджер Бронирований',
            role=roles[1],
            is_active=True
        )
        manager_user.set_password('manager123')
        
        employee_user = User(
            username='employee', 
            email='employee@pool.com', 
            full_name='Сотрудник Бассейна',
            role=roles[2],
            is_active=True
        )
        employee_user.set_password('password123')
        
        db.session.add(admin_user)
        db.session.add(manager_user)
        db.session.add(employee_user)
        
        # Создаем слоты на следующие 30 дней
        today = datetime.now().date()
        for i in range(30):
            slot_date = today + timedelta(days=i)
            daily_slot = DailySlot(
                date=slot_date,
                total_slots=10,
                available_slots=10
            )
            db.session.add(daily_slot)
        
        db.session.commit()

# Настройка Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logging.error(f"Error loading user: {e}")
        return None

# Маршруты
@app.route('/')
@login_required
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error in index route: {e}")
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            logging.info(f"Login attempt for user: {username}")
            logging.info(f"Received password: {password}")
            
            user = User.query.filter_by(username=username).first()
            
            if user is None:
                logging.warning(f"User {username} not found in database")
                flash('Пользователь не найден', 'error')
                return render_template('login.html')
            
            logging.info(f"Found user: {user.username}")
            logging.info(f"Stored password hash: {user.password_hash}")
            
            if user and user.check_password(password):
                login_user(user)
                logging.info(f"User {username} logged in successfully")
                return redirect(url_for('index'))
            
            logging.warning(f"Failed login attempt for user: {username}")
            flash('Неверное имя пользователя или пароль', 'error')
        
        return render_template('login.html')
    except Exception as e:
        logging.error(f"Login error: {e}", exc_info=True)
        flash('Произошла ошибка при входе', 'error')
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    try:
        if not current_user.is_authenticated or current_user.role.name != 'Администратор':
            logging.warning(f"Unauthorized user tried to create a user")
            flash('У вас нет прав для создания пользователей', 'error')
            return redirect(url_for('index'))
        
        roles = Role.query.all()
        
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            full_name = request.form['full_name']
            password = request.form['password']
            role_id = request.form['role_id']
            
            logging.info(f"Attempting to create user: {username}")
            
            # Проверка существования пользователя
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                logging.warning(f"User creation failed: username {username} already exists")
                flash('Пользователь с таким именем уже существует', 'error')
                return render_template('create_user.html', roles=roles)
            
            # Создание нового пользователя
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                role_id=int(role_id),
                is_active=True
            )
            new_user.set_password(password)
            
            try:
                db.session.add(new_user)
                db.session.commit()
                logging.info(f"User {username} created successfully")
                flash(f'Пользователь {username} успешно создан', 'success')
                return redirect(url_for('manage_users'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating user {username}: {e}")
                flash(f'Ошибка при создании пользователя: {str(e)}', 'error')
        
        return render_template('create_user.html', roles=roles)
    except Exception as e:
        logging.error(f"Unexpected error in create_user: {e}")
        flash('Произошла непредвиденная ошибка', 'error')
        return redirect(url_for('index'))

@app.route('/manage_users')
@login_required
def manage_users():
    try:
        if not current_user.is_authenticated or current_user.role.name != 'Администратор':
            logging.warning(f"Unauthorized user tried to access user management")
            flash('У вас нет прав для управления пользователями', 'error')
            return redirect(url_for('index'))
        
        users = User.query.all()
        return render_template('manage_users.html', users=users)
    except Exception as e:
        logging.error(f"Error in manage_users route: {e}")
        flash('Произошла ошибка при загрузке пользователей', 'error')
        return redirect(url_for('index'))

@app.route('/manage_slots', methods=['GET', 'POST'])
@login_required
def manage_slots():
    if not current_user.role.can_manage_slots:
        flash('У вас нет прав для управления днями посещений', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            date_str = request.form['date']
            total_slots = int(request.form['total_slots'])
            reason = request.form.get('reason', '')
            
            # Проверка существования слота
            existing_slot = DailySlot.query.filter_by(date=date_str).first()
            if existing_slot:
                flash('На эту дату уже установлены слоты', 'warning')
            else:
                # Создание нового слота
                new_slot = DailySlot(
                    date=date_str,
                    total_slots=total_slots,
                    available_slots=total_slots,
                    status='Открыт',
                    reason=reason
                )
                db.session.add(new_slot)
                db.session.commit()
                flash('Дни посещений успешно установлены', 'success')
        
        elif action == 'delete':
            slot_id = request.form.get('slot_id')
            slot = DailySlot.query.get(slot_id)
            
            if slot:
                # Проверка, что нет активных бронирований
                active_bookings = Booking.query.filter_by(daily_slot_id=slot.id).filter(Booking.status.in_(['Забронировано', 'Подтверждено'])).count()
                
                if active_bookings > 0:
                    flash('Невозможно удалить слот с активными бронированиями', 'error')
                else:
                    db.session.delete(slot)
                    db.session.commit()
                    flash('Слот успешно удален', 'success')
            else:
                flash('Слот не найден', 'error')
        
        elif action == 'close':
            slot_id = request.form.get('slot_id')
            reason = request.form.get('reason', '')
            slot = DailySlot.query.get(slot_id)
            
            if slot:
                # Проверка, что нет активных бронирований
                active_bookings = Booking.query.filter_by(daily_slot_id=slot.id).filter(Booking.status.in_(['Забронировано', 'Подтверждено'])).count()
                
                if active_bookings > 0:
                    flash('Невозможно закрыть слот с активными бронированиями', 'error')
                else:
                    slot.status = 'Закрыт'
                    slot.reason = reason
                    slot.available_slots = 0
                    db.session.commit()
                    flash('Слот успешно закрыт', 'warning')
            else:
                flash('Слот не найден', 'error')
    
    # Получаем список слотов, отсортированных по дате
    slots = DailySlot.query.order_by(DailySlot.date).all()
    return render_template('manage_slots.html', slots=slots)

@app.route('/manage_subscription', methods=['GET', 'POST'])
@login_required
def manage_subscription():
    if not current_user.role.can_manage_users:
        flash('У вас нет прав для управления абонементами', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            client_id = request.form.get('client_id')
            action = request.form.get('action')
            amount = int(request.form.get('amount', 0))

            client = Client.query.get(client_id)
            if not client:
                flash('Клиент не найден', 'error')
                return redirect(url_for('manage_subscription'))

            # Логирование изменений баланса
            log_entry = SubscriptionLog(
                client_id=client.id,
                action=action,
                amount=amount,
                user_id=current_user.id
            )
            db.session.add(log_entry)

            if action == 'add':
                client.subscription_balance += amount
                flash(f'Добавлено {amount} посещений клиенту {client.name}', 'success')
            elif action == 'subtract':
                if client.subscription_balance >= amount:
                    client.subscription_balance -= amount
                    flash(f'Списано {amount} посещений у клиента {client.name}', 'success')
                else:
                    flash('Недостаточно посещений для списания', 'error')

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при изменении абонемента: {str(e)}', 'error')

    clients = Client.query.all()
    return render_template('manage_subscription.html', clients=clients)

@app.route('/bookings')
@login_required
def bookings():
    # Если пользователь администратор или менеджер, показываем все бронирования
    if current_user.role.can_confirm_visits:
        bookings = Booking.query.filter(
            Booking.status.in_(['Забронировано', 'Подтверждено'])
        ).order_by(Booking.id.desc()).all()
    else:
        # Для обычных пользователей - только их собственные бронирования
        bookings = Booking.query.filter(
            Booking.client_id == current_user.id,
            Booking.status.in_(['Забронировано', 'Подтверждено', 'Посещено'])
        ).order_by(Booking.id.desc()).all()
    
    return render_template('bookings.html', bookings=bookings)

@app.route('/confirm_booking/<int:booking_id>', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    if not current_user.role.can_confirm_visits:
        flash('У вас нет прав для подтверждения бронирований', 'error')
        return redirect(url_for('bookings'))

    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Подтверждено'
    booking.confirmed_by_id = current_user.id
    db.session.commit()
    flash('Бронирование подтверждено', 'success')
    return redirect(url_for('bookings'))

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем права пользователя
    if booking.client_id != current_user.id:
        flash('У вас нет прав для отмены этого бронирования', 'error')
        return redirect(url_for('bookings'))
    
    # Возвращаем слот и баланс
    slot = booking.daily_slot
    client = booking.client
    
    # Проверяем, можно ли отменить бронирование
    if booking.status not in ['Забронировано', 'Подтверждено']:
        flash('Бронирование нельзя отменить', 'error')
        return redirect(url_for('bookings'))
    
    # Возвращаем слот и баланс
    slot.available_slots += 1
    client.subscription_balance += 1
    
    # Обновляем статус бронирования
    booking.status = 'Отменено'
    
    db.session.commit()
    
    flash('Бронирование отменено', 'success')
    return redirect(url_for('bookings'))

@app.route('/complete_booking/<int:booking_id>', methods=['POST'])
@login_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем права пользователя
    if booking.client_id != current_user.id:
        flash('У вас нет прав для списания этого посещения', 'error')
        return redirect(url_for('bookings'))
    
    # Проверяем статус бронирования
    if booking.status != 'Подтверждено':
        flash('Посещение можно списать только для подтвержденного бронирования', 'error')
        return redirect(url_for('bookings'))
    
    # Обновляем статус бронирования
    booking.status = 'Посещено'
    
    db.session.commit()
    
    flash('Посещение списано', 'success')
    return redirect(url_for('bookings'))

@app.route('/complete_visit/<int:booking_id>', methods=['POST'])
@login_required
def complete_visit(booking_id):
    if not current_user.role.can_confirm_visits:
        flash('У вас нет прав для подтверждения посещений', 'error')
        return redirect(url_for('bookings'))

    booking = Booking.query.get_or_404(booking_id)
    client = Client.query.get(booking.client_id)
    
    # Создаем запись о посещении
    new_visit = Visit(
        client_id=client.id,
        visit_date=datetime.now(),
        booking_id=booking.id,
        confirmed_by_id=current_user.id
    )
    
    # Списываем посещение
    client.subscription_balance -= 1
    
    # Обновляем статус бронирования
    booking.status = 'Посещено'
    
    db.session.add(new_visit)
    db.session.commit()
    
    flash('Посещение подтверждено и списано с абонемента', 'success')
    return redirect(url_for('bookings'))

@app.route('/cancel_visit/<int:booking_id>', methods=['POST'])
@login_required
def cancel_visit(booking_id):
    if not current_user.role.can_confirm_visits:
        flash('У вас нет прав для отмены посещений', 'error')
        return redirect(url_for('bookings'))

    booking = Booking.query.get_or_404(booking_id)
    client = Client.query.get(booking.client_id)
    daily_slot = DailySlot.query.get(booking.daily_slot_id)
    
    # Возвращаем слот
    daily_slot.available_slots += 1
    
    # Возвращаем посещение в абонемент
    client.subscription_balance += 1
    
    # Обновляем статус бронирования
    booking.status = 'Отменено'
    
    db.session.commit()
    
    flash('Посещение отменено, слот возвращен, посещение зачтено обратно в абонемент', 'warning')
    return redirect(url_for('bookings'))

@app.route('/admin_confirm_booking/<int:booking_id>', methods=['POST'])
@login_required
def admin_confirm_booking(booking_id):
    if not current_user.role.can_confirm_visits:
        flash('У вас нет прав для подтверждения бронирований', 'error')
        return redirect(url_for('bookings'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем статус бронирования
    if booking.status != 'Забронировано':
        flash('Бронирование можно подтвердить только в статусе "Забронировано"', 'error')
        return redirect(url_for('bookings'))
    
    # Обновляем статус бронирования
    booking.status = 'Подтверждено'
    booking.confirmed_by_id = current_user.id
    
    db.session.commit()
    
    flash('Бронирование подтверждено', 'success')
    return redirect(url_for('bookings'))

@app.route('/admin_cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def admin_cancel_booking(booking_id):
    if not current_user.role.can_confirm_visits:
        flash('У вас нет прав для отмены бронирований', 'error')
        return redirect(url_for('bookings'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверяем статус бронирования
    if booking.status not in ['Забронировано', 'Подтверждено']:
        flash('Бронирование нельзя отменить', 'error')
        return redirect(url_for('bookings'))
    
    # Возвращаем слот и баланс
    slot = booking.daily_slot
    client = booking.client
    
    # Возвращаем слот и баланс
    slot.available_slots += 1
    client.subscription_balance += 1
    
    # Обновляем статус бронирования
    booking.status = 'Отменено'
    booking.confirmed_by_id = current_user.id
    
    db.session.commit()
    
    flash('Бронирование отменено', 'success')
    return redirect(url_for('bookings'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_db()
    app.run(debug=True)
