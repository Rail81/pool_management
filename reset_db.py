from app import app, db
from models import Role, User

def reset_database():
    with app.app_context():
        # Удаляем все существующие таблицы
        db.drop_all()
        
        # Создаем новые таблицы
        db.create_all()
        
        # Создаем роли
        roles = [
            Role(name='Администратор', description='Полный доступ', 
                 can_manage_users=True, can_manage_slots=True, can_confirm_visits=True),
            Role(name='Менеджер', description='Управление бронированиями', 
                 can_manage_users=False, can_manage_slots=True, can_confirm_visits=False),
            Role(name='Сотрудник', description='Базовый доступ', 
                 can_manage_users=False, can_manage_slots=False, can_confirm_visits=False)
        ]
        
        db.session.add_all(roles)
        
        # Создаем администратора
        admin = User(
            username='admin',
            email='admin@pool.com',
            full_name='Администратор Системы',
            role_id=1,
            is_active=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("База данных сброшена и инициализирована.")

if __name__ == '__main__':
    reset_database()
