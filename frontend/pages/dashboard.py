# frontend/pages/dashboard.py
from nicegui import ui
from backend.db import SessionLocal
from backend.models import Key, User
import secrets


def get_user_keys(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Key).filter(Key.user_id == user_id).all()
    finally:
        db.close()


def create_key(user_id: int, description: str):
    db = SessionLocal()
    try:
        new_key = Key(
            user_id=user_id,
            key_value=secrets.token_hex(16),
            description=description
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
def dashboard_page(user_id: int = 1):
    ui.label("Панель управления ключами").classes("text-3xl font-bold text-center mt-6 mb-4")

    with ui.card().classes("max-w-3xl mx-auto p-6 shadow-lg flex flex-col gap-4"):
        ui.label("🔑 Добавить новый ключ").classes("text-xl font-semibold")

        key_desc = ui.input("Описание ключа").props("outlined").classes("w-full")

        def add_key():
            if not key_desc.value.strip():
                ui.notify("Введите описание", color="warning")
                return
            new_key = create_key(user_id, key_desc.value.strip())
            ui.notify(f"Ключ создан: {new_key.key_value}", color="positive")
            key_desc.value = ""
            refresh_keys()

        ui.button("Создать ключ", on_click=add_key).classes("bg-blue-500 text-white rounded-lg shadow hover:bg-blue-600 w-40")

        ui.separator().classes("my-4")

        key_container = ui.column().classes("w-full gap-2")

        def refresh_keys():
            key_container.clear()
            keys = get_user_keys(user_id)
            if not keys:
                key_container.add(ui.label("У вас пока нет ключей").classes("text-gray-500 italic"))
                return
            for k in keys:
                with key_container:
                    with ui.row().classes("w-full justify-between items-center border p-2 rounded-lg"):
                        ui.label(f"{k.description or '(Без описания)'} — {k.key_value}").classes("font-mono")
                        ui.button("Удалить", icon="delete", color="red", on_click=lambda kid=k.id: (delete_key(kid), refresh_keys()))

        refresh_keys()
