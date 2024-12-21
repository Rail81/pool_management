import sys
import locale

# Устанавливаем кодировку
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

sys.path.append('.')

from app import app, db
from models import User, Role

def debug_users():
    with app.app_context():
        # Проверка ролей
        roles = Role.query.all()
        print("Доступные роли:")
        for role in roles:
            print(f"ID: {role.id}, Название: {role.name}")
        
        # Проверка пользователей
        users = User.query.all()
        print("\nПользователи:")
        for u in users:
            print(f"ID: {u.id}")
            print(f"Username: {u.username}")
            print(f"Email: {u.email}")
            print(f"Role ID: {u.role_id}")
            print(f"Role Name: {u.role.name if u.role else 'Нет роли'}")
            print(f"Is Active: {u.is_active}")
            print("---")

if __name__ == '__main__':
    debug_users()
