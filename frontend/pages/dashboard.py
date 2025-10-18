<<<<<<< HEAD
from nicegui import ui, app
from backend.db import SessionLocal
from backend.models import Key, User
import datetime

def get_user_from_db(user_id: int):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

def verify_master_key(user_id: int, master_key: str) -> bool:
    """Проверяет мастер-ключ пользователя"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user and user.master_key == master_key
    finally:
        db.close()

def set_master_key(user_id: int, master_key: str):
    """Устанавливает мастер-ключ пользователю"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.master_key = master_key
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_user_keys(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Key).filter(Key.user_id == user_id).all()
    finally:
        db.close()

def create_key(user_id: int, key_name: str, key_value: str, description: str = ""):
    db = SessionLocal()
    try:
        new_key = Key(
            user_id=user_id,
            key_name=key_name,
            key_value=key_value,
            description=description,
            created_at=datetime.datetime.now()
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key
    finally:
        db.close()

def delete_key(key_id: int):
    db = SessionLocal()
    try:
        key = db.query(Key).filter(Key.id == key_id).first()
        if key:
            db.delete(key)
            db.commit()
            return True
        return False
    finally:
        db.close()

@ui.page("/dashboard")
def dashboard_page():
    # Получаем user_id из query параметров
    try:
        user_id = int(ui.context.client.query_params.get('user_id', 1))
    except:
        user_id = 1

    user = get_user_from_db(user_id)
    
    # Если пользователь не найден
    if not user:
        with ui.card().classes("max-w-md mx-auto mt-20 p-6"):
            ui.label("❌ Ошибка").classes("text-xl font-bold mb-4")
            ui.label("Пользователь не найден").classes("text-gray-600 mb-4")
            ui.button("← Назад", on_click=lambda: ui.navigate.to("/")).classes("w-full")
        return
    
    # Если у пользователя нет мастер-ключа, просим установить
    if not user.master_key:
        with ui.card().classes("max-w-md mx-auto mt-20 p-6"):
            ui.label("🔐 Установите мастер-ключ").classes("text-xl font-bold mb-4")
            ui.label("Этот ключ будет использоваться для доступа к панели управления API ключами").classes("text-gray-600 mb-4")
            
            master_key_input = ui.input("Мастер-ключ", password=True).classes("w-full mb-4")
            confirm_key_input = ui.input("Подтвердите мастер-ключ", password=True).classes("w-full mb-4")
            
            def set_key():
                if not master_key_input.value:
                    ui.notify("Введите мастер-ключ", color="warning")
                    return
                if master_key_input.value != confirm_key_input.value:
                    ui.notify("Ключи не совпадают", color="warning")
                    return
                
                set_master_key(user_id, master_key_input.value)
                ui.notify("Мастер-ключ установлен", color="positive")
                ui.navigate.reload()
            
            ui.button("Установить мастер-ключ", on_click=set_key).classes("w-full bg-blue-500 text-white")
            ui.button("← Назад в профиль", 
                     on_click=lambda: ui.navigate.to(f"/profile?user_id={user_id}")).classes("w-full mt-2")
        return
    
    # Используем session storage для отслеживания аутентификации
    if not app.storage.session.get('master_key_authenticated', False):
        with ui.card().classes("max-w-md mx-auto mt-20 p-6"):
            ui.label("🔐 Введите мастер-ключ").classes("text-xl font-bold mb-4")
            master_key_input = ui.input("Мастер-ключ", password=True).classes("w-full mb-4")
            
            def check_master_key():
                if verify_master_key(user_id, master_key_input.value):
                    app.storage.session['master_key_authenticated'] = True
                    ui.navigate.reload()
                else:
                    ui.notify("Неверный мастер-ключ", color="negative")
            
            ui.button("Войти", on_click=check_master_key).classes("w-full bg-green-500 text-white")
            ui.button("← Назад в профиль", 
                     on_click=lambda: ui.navigate.to(f"/profile?user_id={user_id}")).classes("w-full mt-2")
        return

    # Основной интерфейс dashboard
    with ui.column().classes("w-full"):
        # Кнопка возврата в профиль и выхода
        with ui.row().classes("w-full justify-between p-4"):
            ui.button("← Назад в профиль", 
                     on_click=lambda: ui.navigate.to(f"/profile?user_id={user_id}")).props("flat").classes("text-blue-600")
            ui.button("Выйти из панели", 
                     on_click=lambda: (app.storage.session.pop('master_key_authenticated', None), ui.navigate.reload())).props("flat").classes("text-red-600")

        ui.label("Панель управления API ключами").classes("text-3xl font-bold text-center mt-6 mb-4")

        with ui.card().classes("max-w-3xl mx-auto p-6 shadow-lg flex flex-col gap-4"):
            ui.label("🔑 Добавить новый API ключ").classes("text-xl font-semibold")

            key_name_input = ui.input("Название ключа").props("outlined").classes("w-full")
            key_value_input = ui.input("API ключ").props("outlined").classes("w-full")
            key_desc_input = ui.input("Описание (опционально)").props("outlined").classes("w-full")

            def add_key():
                if not key_name_input.value.strip():
                    ui.notify("Введите название ключа", color="warning")
                    return
                if not key_value_input.value.strip():
                    ui.notify("Введите API ключ", color="warning")
                    return
                
                new_key = create_key(user_id, key_name_input.value.strip(), key_value_input.value.strip(), key_desc_input.value.strip())
                ui.notify(f"Ключ '{new_key.key_name}' добавлен", color="positive")
                key_name_input.value = ""
                key_value_input.value = ""
                key_desc_input.value = ""
                refresh_keys()

            ui.button("Добавить ключ", on_click=add_key, icon="add").classes("bg-green-500 text-white rounded-lg shadow hover:bg-green-600 w-48")

            ui.separator().classes("my-4")

            key_container = ui.column().classes("w-full gap-3")

            def refresh_keys():
                key_container.clear()
                keys = get_user_keys(user_id)
                if not keys:
                    with key_container:
                        ui.label("У вас пока нет API ключей").classes("text-gray-500 italic text-center p-8")
                    return
                    
                with key_container:
                    for key in keys:
                        with ui.card().classes("w-full p-4 border-l-4 border-green-500"):
                            with ui.row().classes("w-full justify-between items-center"):
                                with ui.column().classes("gap-1 flex-1"):
                                    ui.label(key.key_name).classes("font-semibold text-lg")
                                    if key.description:
                                        ui.label(key.description).classes("text-sm text-gray-600")
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label("Ключ:").classes("text-sm text-gray-600")
                                        ui.label(f"{key.key_value[:12]}...").classes("font-mono text-sm bg-gray-100 px-2 py-1 rounded")
                                    ui.label(f"Создан: {key.created_at.strftime('%d.%m.%Y %H:%M')}").classes("text-xs text-gray-500")
                                
                                with ui.row().classes("gap-2"):
                                    # Кнопка копирования
                                    def copy_key(key_value):
                                        ui.run_javascript(f"navigator.clipboard.writeText('{key_value}')")
                                        ui.notify("Ключ скопирован", color="info")
                                    
                                    ui.button(icon="content_copy", on_click=lambda k=key: copy_key(k.key_value)).props("outline")
                                    
                                    # Кнопка удаления
                                    ui.button(icon="delete", color="red", 
                                             on_click=lambda k=key: (delete_key(k.id), refresh_keys())).props("outline")

            refresh_keys()

            # Статистика ключей
            keys = get_user_keys(user_id)
            active_keys = [k for k in keys if k.is_active]
            
            with ui.row().classes("w-full justify-around mt-4 p-4 bg-gray-50 rounded-lg"):
                ui.label(f"Всего ключей: {len(keys)}").classes("font-semibold")
                ui.label(f"Активных: {len(active_keys)}").classes("text-green-600 font-semibold")
                ui.label(f"Неактивных: {len(keys) - len(active_keys)}").classes("text-orange-600 font-semibold")
=======
>>>>>>> parent of eeb9efe (New Reworked system)
