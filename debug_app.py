from app import app, db
from models import Role, User
import traceback
import sys

def full_debug():
    try:
        with app.app_context():
            # Настройка кодировки
            sys.stdout.reconfigure(encoding='utf-8')
            
            # Проверка базы данных
            print("Проверка базы данных:")
            print(f"Движок базы данных: {db.engine}")
            
            # Проверка ролей
            print("\nПроверка ролей:")
            roles = Role.query.all()
            for role in roles:
                print(f"ID: {role.id}, Название: {role.name}")
            
            # Проверка пользователей
            print("\nПроверка пользователей:")
            users = User.query.all()
            for user in users:
                print(f"ID: {user.id}, Username: {user.username}, Role: {user.role.name if user.role else 'Без роли'}")
    
    except Exception as e:
        print("Произошла ошибка:")
        print(traceback.format_exc())

if __name__ == '__main__':
    full_debug()
