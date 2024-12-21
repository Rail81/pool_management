#!/bin/bash

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых зависимостей
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    docker.io \
    docker-compose

# Клонирование репозитория
git clone https://github.com/yourusername/pool_management.git
cd pool_management

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Сборка и запуск контейнеров
docker-compose up --build -d

# Первоначальная настройка базы данных
docker-compose exec web python init_db.py

echo "Установка завершена. Приложение доступно на порту 5000."
