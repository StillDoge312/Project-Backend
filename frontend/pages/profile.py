from nicegui import ui
from backend.db import SessionLocal
from backend.models import User

def get_user_from_db(user_id: int):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

def update_email(user_id: int, new_email: str):
    db = SessionLocal()
    try:
        # Проверяем, есть ли пользователь с таким email (и не он сам)
        existing_user = db.query(User).filter(User.email == new_email, User.id != user_id).first()
        if existing_user:
            return "exists"

        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email = new_email
            db.commit()
            db.refresh(user)
            return True
        return False
    finally:
        db.close()

@ui.page("/profile")
async def profile_page():
    import asyncio
    await asyncio.sleep(0.2)
    
    # Получаем user_id из query параметров
    try:
        user_id = int(ui.context.client.query_params.get('user_id', 1))
    except:
        user_id = 1

    user = get_user_from_db(user_id)

    with ui.row().classes("w-full justify-end p-4"):
        with ui.menu() as menu:
            with ui.column().classes("p-4 gap-2"):
                ui.label("⚙️ Настройки").classes("text-lg font-bold mb-2")

                email_input = ui.input(
                    "Email", value=user.email if user and user.email else ""
                ).classes("w-64")

                def save_email():
                    result = update_email(user_id, email_input.value)
                    if result == True:
                        ui.notify("Email обновлён", color="positive")
                        menu.close()
                    elif result == "exists":
                        ui.notify("Такой email уже зарегистрирован", color="warning")
                    else:
                        ui.notify("Ошибка при сохранении", color="negative")

                ui.button("Сохранить", on_click=save_email).props("outline").classes("text-green-600")
                ui.button("Закрыть", on_click=menu.close).props("flat")

        ui.button(icon="settings", on_click=menu.open).props("flat round").classes("text-gray-700")

    with ui.card().classes("max-w-lg mx-auto mt-10 p-6 shadow-lg flex flex-col gap-4 items-center"):
        ui.label("Профиль").classes("text-3xl font-bold mb-2")
        ui.avatar(icon="account_circle", size="80px").classes("mb-4 text-blue-600")

        if user:
            ui.label(f"👤 Имя пользователя: {user.username}").classes("text-lg")
            ui.label(f"📧 Email: {user.email if user.email else 'Не указан'}").classes("text-lg")
            ui.label(f"🔐 Мастер-ключ: {'Установлен' if user.master_key else 'Не установлен'}").classes("text-lg")
            ui.label(f"📅 Дата регистрации: {user.created_at}").classes("text-lg")
        else:
            ui.label("Пользователь не найден").classes("text-red-500")

        ui.separator().classes("my-4 w-full")
        
        # Кнопка перехода в Dashboard
        with ui.row().classes("w-full gap-2"):
            ui.button("🔑 Управление API ключами", 
                     on_click=lambda: ui.navigate.to(f"/dashboard?user_id={user_id}")).props(
                "outline unelevated no-caps"
            ).classes("flex-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg shadow-md")
            
            ui.button("Выйти", on_click=lambda: ui.navigate.to("/")).props(
                "flat unelevated no-caps"
            ).classes("flex-1 bg-red-500 text-white hover:bg-red-600 rounded-lg shadow-md")