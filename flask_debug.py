from flask import Flask
from flask_login import LoginManager
from models import db, User, Role
import os

def create_app():
    app = Flask(__name__)
    
    # Настройки базы данных
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pool.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализация расширений
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Создание контекста приложения
    with app.app_context():
        try:
            # Создание таблиц
            db.create_all()
            
            # Проверка существования ролей
            existing_roles = Role.query.count()
            if existing_roles == 0:
                roles = [
                    Role(name='Администратор', description='Полный доступ', 
                         can_manage_users=True, can_manage_slots=True, can_confirm_visits=True),
                    Role(name='Менеджер', description='Управление бронированиями', 
                         can_manage_users=False, can_manage_slots=True, can_confirm_visits=False),
                    Role(name='Сотрудник', description='Базовый доступ', 
                         can_manage_users=False, can_manage_slots=False, can_confirm_visits=False)
                ]
                db.session.add_all(roles)
                db.session.commit()
            
            # Проверка существования администратора
            admin_exists = User.query.filter_by(username='admin').first()
            if not admin_exists:
                admin_role = Role.query.filter_by(name='Администратор').first()
                admin = User(
                    username='admin',
                    email='admin@pool.com',
                    full_name='Администратор Системы',
                    role_id=admin_role.id,
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            
            print("Инициализация базы данных успешна.")
        
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
