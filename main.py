import os
from nicegui import ui, app
from backend import api
from backend.db import engine, Base
import sqlite3

def check_and_migrate():
    """Проверяет и обновляет структуру базы данных при необходимости"""
    if not os.path.exists("data/app.db"):
        return  # База создастся автоматически
        
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем существующие столбцы
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем недостающие столбцы
        if 'master_key' not in columns:
            print("Добавляем столбец master_key...")
            cursor.execute("ALTER TABLE users ADD COLUMN master_key VARCHAR")
            conn.commit()
            
        if 'email' not in columns:
            print("Добавляем столбец email...")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
            conn.commit()
            
    except Exception as e:
        print(f"Ошибка миграции: {e}")
    finally:
        conn.close()

os.makedirs("data", exist_ok=True)

# Проверяем и мигрируем базу перед созданием таблиц
check_and_migrate()

# Создаем таблицы (это безопасно - существующие таблицы не затрагиваются)
Base.metadata.create_all(bind=engine)

app.include_router(api.router)

import frontend.pages.login
import frontend.pages.register
import frontend.pages.profile
import frontend.pages.dashboard

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8000, reload=True)