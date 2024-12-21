import os
import sys
import traceback

def debug_environment():
    print("Python Version:", sys.version)
    print("Python Executable:", sys.executable)
    print("Current Working Directory:", os.getcwd())
    print("Python Path:", sys.path)
    
    # Проверка зависимостей
    try:
        import flask
        import flask_login
        import sqlalchemy
        print("\nВерсии библиотек:")
        print("Flask:", flask.__version__)
        print("Flask-Login:", flask_login.__version__)
        print("SQLAlchemy:", sqlalchemy.__version__)
    except ImportError as e:
        print("Ошибка импорта библиотек:", e)

def debug_flask_app():
    try:
        from flask import Flask
        from flask_login import LoginManager
        from models import db, User, Role
        
        app = Flask(__name__)
        
        # Настройки базы данных
        app.config['SECRET_KEY'] = 'debug_secret_key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pool.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEBUG'] = True
        
        # Инициализация расширений
        db.init_app(app)
        login_manager = LoginManager(app)
        login_manager.login_view = 'login'
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Создание контекста приложения
        with app.app_context():
            # Создание таблиц
            db.create_all()
            
            # Проверка и создание ролей
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
            
            # Проверка и создание администратора
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
            
            print("\nПроверка базы данных:")
            print("Роли:", Role.query.all())
            print("Пользователи:", User.query.all())
    
    except Exception as e:
        print("\nПроизошла критическая ошибка:")
        print(traceback.format_exc())

def main():
    debug_environment()
    debug_flask_app()

if __name__ == '__main__':
    main()
