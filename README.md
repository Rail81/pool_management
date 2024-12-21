# Система Управления Бассейном

## Описание
Веб-приложение и Telegram-бот для управления бронированием и посещением бассейна.

## Возможности
- Регистрация пользователей
- Бронирование слотов
- Управление абонементами
- Telegram-бот для взаимодействия

## Требования
- Python 3.9+
- Docker
- Docker Compose

## Установка на Debian 11

### Подготовка
1. Клонируйте репозиторий
```bash
git clone https://github.com/yourusername/pool_management.git
cd pool_management
```

2. Создайте файл `.env` на основе `example.env`
```bash
cp example.env .env
```

3. Отредактируйте `.env` с вашими настройками

### Установка через Docker
```bash
docker-compose up --build -d
```

### Первоначальная настройка
```bash
docker-compose exec web python init_db.py
```

## Развертывание
- Веб-приложение: http://localhost:5000
- Telegram-бот: запустите через Telegram

## Лицензия
MIT License
