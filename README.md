# Система управления бассейном

Система для управления посещениями бассейна с веб-интерфейсом для администраторов и Telegram ботом для клиентов.

## Требования к системе

- Debian 11
- Python 3.8+
- Nginx
- Supervisor

## Установка

1. Склонируйте репозиторий:
```bash
git clone https://github.com/sardude/pool_management.git
cd pool_management
```

2. Создайте файл .env с необходимыми переменными окружения:
```bash
TELEGRAM_TOKEN=ваш_токен_бота
FLASK_SECRET_KEY=ваш_секретный_ключ
```

3. Запустите установочный скрипт:
```bash
chmod +x install.sh
sudo ./install.sh
```

4. После установки проверьте работу сервисов:
```bash
sudo supervisorctl status
```

## Доступ к системе

### Веб-интерфейс
- URL: http://ваш_домен
- Администратор:
  - Логин: admin
  - Пароль: admin123
- Пользователь:
  - Логин: user
  - Пароль: user123

### Telegram бот
Найдите бота по имени и начните с ним работу, отправив команду /start

## Функциональность

### Администратор (admin)
- Управление местами в бассейне
- Просмотр истории посещений
- Управление клиентами
- Добавление и списание посещений
- Удаление клиентов

### Пользователь (user)
- Просмотр списка клиентов
- Списание посещений

### Telegram бот
- Регистрация новых клиентов
- Просмотр доступных дней
- Бронирование посещений
- Проверка баланса абонемента

## Логи

- Веб-приложение: /var/log/pool_flask.{out,err}.log
- Telegram бот: /var/log/pool_bot.{out,err}.log
- Nginx: /var/log/nginx/access.log и error.log

## Обслуживание

Для перезапуска сервисов:
```bash
sudo supervisorctl restart pool_flask
sudo supervisorctl restart pool_bot
```

Для просмотра логов:
```bash
tail -f /var/log/pool_flask.out.log
tail -f /var/log/pool_bot.out.log
