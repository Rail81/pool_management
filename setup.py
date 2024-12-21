import os
import sys
from dotenv import load_dotenv
from app import app, db
from models import Role, User, Client, DailySlot
from datetime import datetime, timedelta

def setup_database():
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
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
        
        # Создаем администратора
        admin = User(
            username='admin', 
            email='admin@pool.com', 
            full_name='Главный Администратор',
            role=roles[0],
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Создаем слоты на следующие 30 дней
        today = datetime.now().date()
        slots = [
            DailySlot(
                date=today + timedelta(days=i), 
                total_slots=20, 
                available_slots=20
            ) for i in range(30)
        ]
        
        db.session.add_all(slots)
        db.session.commit()

if __name__ == '__main__':
    setup_database()
    print("База данных успешно инициализирована!")
