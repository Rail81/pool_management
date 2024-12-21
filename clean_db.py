from app import app, db
from models import DailySlot
from sqlalchemy import func

def clean_duplicate_slots():
    with app.app_context():
        # Находим дубликаты слотов
        duplicates = (
            db.session.query(DailySlot.date, func.count(DailySlot.id))
            .group_by(DailySlot.date)
            .having(func.count(DailySlot.id) > 1)
            .all()
        )
        
        print("Найдены дубликаты дат:", duplicates)
        
        # Удаляем дубликаты, оставляя первую запись
        for date, count in duplicates:
            # Находим все записи для этой даты
            slots = DailySlot.query.filter_by(date=date).order_by(DailySlot.id).all()
            
            # Оставляем первую запись, удаляем остальные
            for slot in slots[1:]:
                print(f"Удаляем дубликат слота: {slot.id}, {slot.date}")
                db.session.delete(slot)
        
        # Коммитим изменения
        db.session.commit()
        print("Дубликаты слотов удалены.")

def reset_slot_availability():
    with app.app_context():
        # Сбрасываем доступность слотов к изначальному состоянию
        slots = DailySlot.query.all()
        for slot in slots:
            slot.available_slots = slot.total_slots
        
        db.session.commit()
        print("Доступность слотов сброшена.")

if __name__ == '__main__':
    clean_duplicate_slots()
    reset_slot_availability()
