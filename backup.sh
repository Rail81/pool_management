#!/bin/bash

# Создаем директорию для бэкапов если её нет
mkdir -p /opt/pool_management/backups

# Имя файла бэкапа с текущей датой
BACKUP_FILE="/opt/pool_management/backups/pool_$(date +%Y%m%d_%H%M%S).db"

# Копируем базу данных
cp /opt/pool_management/pool.db "$BACKUP_FILE"

# Сжимаем бэкап
gzip "$BACKUP_FILE"

# Удаляем бэкапы старше 30 дней
find /opt/pool_management/backups -name "pool_*.db.gz" -mtime +30 -delete

echo "Backup created: ${BACKUP_FILE}.gz"
