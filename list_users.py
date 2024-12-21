import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from app import User, Role

def print_users():
    with app.app_context():
        users = User.query.all()
        print("\nСписок пользователей:")
        for u in users:
            print(f"ID: {u.id}")
            print(f"Имя пользователя: {u.username}")
            print(f"Email: {u.email}")
            print(f"ФИО: {u.full_name}")
            print(f"Роль: {u.role.name}")
            print(f"Статус: {'Активен' if u.is_active else 'Заблокирован'}")
            print("---")

if __name__ == '__main__':
    print_users()
