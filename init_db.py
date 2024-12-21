from app import app, db
from models import Role, User, DailySlot
from datetime import datetime, timedelta

def create_daily_slots():
    # Создаем слоты на следующие 30 дней
    today = datetime.now().date()
    for i in range(30):
        slot_date = today + timedelta(days=i)
        daily_slot = DailySlot(
            date=slot_date,
            total_slots=10,  # Максимальное количество мест
            available_slots=10  # Изначально все места свободны
        )
        db.session.add(daily_slot)
    
    db.session.commit()

def init_roles_and_users():
    # Создание ролей
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
    
    db.session.commit()

def main():
    with app.app_context():
        db.create_all()  # Создаем все таблицы
        init_roles_and_users()
        create_daily_slots()

if __name__ == '__main__':
    main()
