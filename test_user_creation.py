import logging
import requests
import json
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация теста
BASE_URL = 'http://localhost:5000'
TEST_USERNAME = 'test_employee'
TEST_EMAIL = 'test_employee@pool.com'
TEST_FULL_NAME = 'Тестовый Сотрудник'
TEST_PASSWORD = 'test_password123'

def test_login():
    """Тест входа администратора"""
    try:
        # Создание сессии для сохранения куки
        session = requests.Session()
        
        # Данные для входа
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # Попытка входа
        login_response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=True)
        logging.info(f"Login attempt for user: admin")
        logging.debug(f"Login response status: {login_response.status_code}")
        
        # Проверка успешности входа
        if login_response.status_code != 200:
            logging.error(f"Login failed. Status code: {login_response.status_code}")
            logging.debug(f"Login response content: {login_response.text}")
            return None
        
        return session
    except Exception as e:
        logging.error(f"Login error: {e}")
        return None

def test_create_user(session):
    """Тест создания нового пользователя"""
    try:
        # Получение списка ролей
        roles_response = session.get(f'{BASE_URL}/create_user')
        roles = roles_response.text
        
        # Данные для создания пользователя
        user_data = {
            'username': TEST_USERNAME,
            'email': TEST_EMAIL,
            'full_name': TEST_FULL_NAME,
            'password': TEST_PASSWORD,
            'role_id': 3  # ID роли "Сотрудник"
        }
        
        # Попытка создания пользователя
        create_response = session.post(f'{BASE_URL}/create_user', data=user_data, allow_redirects=True)
        logging.info(f"Attempting to create user: {TEST_USERNAME}")
        
        # Проверка успешности создания
        if create_response.status_code == 200:
            logging.info(f"User {TEST_USERNAME} created successfully")
            return True
        else:
            logging.error(f"User creation failed. Status code: {create_response.status_code}")
            logging.debug(f"Create user response content: {create_response.text}")
            return False
    except Exception as e:
        logging.error(f"User creation error: {e}")
        return False

def test_login_new_user():
    """Тест входа нового пользователя"""
    try:
        # Создание сессии
        session = requests.Session()
        
        # Данные для входа нового пользователя
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
        
        # Попытка входа
        login_response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=True)
        logging.info(f"Login attempt for new user: {TEST_USERNAME}")
        
        # Проверка успешности входа
        if login_response.status_code == 200:
            logging.info(f"New user {TEST_USERNAME} logged in successfully")
            return True
        else:
            logging.error(f"New user login failed. Status code: {login_response.status_code}")
            logging.debug(f"New user login response content: {login_response.text}")
            return False
    except Exception as e:
        logging.error(f"New user login error: {e}")
        return False

def run_tests():
    """Выполнение всех тестов"""
    # Тест 1: Вход администратора
    admin_session = test_login()
    if not admin_session:
        logging.error("Admin login test failed")
        return
    
    # Тест 2: Создание пользователя
    user_created = test_create_user(admin_session)
    if not user_created:
        logging.error("User creation test failed")
        return
    
    # Тест 3: Вход нового пользователя
    new_user_login = test_login_new_user()
    if not new_user_login:
        logging.error("New user login test failed")
        return
    
    logging.info("All tests passed successfully!")

if __name__ == '__main__':
    run_tests()
