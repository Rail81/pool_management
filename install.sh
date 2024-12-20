#!/bin/bash

# Обновление системы
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
apt-get install -y python3 python3-pip python3-venv nginx supervisor

# Создание пользователя для приложения
useradd -m -s /bin/bash poolapp

# Создание директории для приложения
mkdir -p /opt/pool_management
cp -r * /opt/pool_management/
chown -R poolapp:poolapp /opt/pool_management

# Создание виртуального окружения и установка зависимостей
cd /opt/pool_management
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создание конфигурации для supervisor
cat > /etc/supervisor/conf.d/pool_management.conf << EOL
[program:pool_flask]
command=/opt/pool_management/venv/bin/python /opt/pool_management/app.py
directory=/opt/pool_management
user=poolapp
autostart=true
autorestart=true
stderr_logfile=/var/log/pool_flask.err.log
stdout_logfile=/var/log/pool_flask.out.log

[program:pool_bot]
command=/opt/pool_management/venv/bin/python /opt/pool_management/bot.py
directory=/opt/pool_management
user=poolapp
autostart=true
autorestart=true
stderr_logfile=/var/log/pool_bot.err.log
stdout_logfile=/var/log/pool_bot.out.log
EOL

# Создание конфигурации для nginx
cat > /etc/nginx/sites-available/pool_management << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

# Активация конфигурации nginx
ln -s /etc/nginx/sites-available/pool_management /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Перезапуск сервисов
systemctl restart nginx
supervisorctl reread
supervisorctl update
supervisorctl restart all

echo "Установка завершена!"
