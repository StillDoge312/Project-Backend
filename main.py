import os
from nicegui import ui
from backend.db import engine, Base
from backend.models import User, Key  # Явный импорт моделей

def initialize_database():
    """Инициализация базы данных с проверкой"""
    print("🔄 Инициализация базы данных...")
    
    # Создаем директорию
    os.makedirs("data", exist_ok=True)
    
    try:
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы успешно!")
        
        # Проверяем создание таблиц
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Созданные таблицы: {tables}")
        
        if 'users' in tables:
            print("✅ Таблица 'users' существует")
        else:
            print("❌ Таблица 'users' не создана!")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы: {e}")
        return False

# Инициализируем базу ДО импорта страниц
if initialize_database():
    print("🚀 Запуск приложения...")
    
    # Импортируем страницы
    import frontend.pages.login
    import frontend.pages.register  
    import frontend.pages.profile
    import frontend.pages.dashboard
    
    # Запускаем приложение
    ui.run(host="0.0.0.0", port=8000, reload=False)
else:
    print("💥 Не удалось инициализировать базу данных")