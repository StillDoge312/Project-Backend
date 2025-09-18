# frontend/pages/register.py
from nicegui import ui
from backend.auth import create_user

@ui.page("/register")
def register_page():
    with ui.card().classes("w-80 mx-auto mt-20 p-6 shadow-lg"):
        ui.label("Регистрация").classes("text-2xl mb-4")

        username_input = ui.input("Логин").classes("w-full mb-2")
        password_input = ui.input("Пароль", password=True, password_toggle_button=True).classes("w-full mb-2")

        def handle_register():
            username = (username_input.value or "").strip()
            password = password_input.value or ""
            if not username or not password:
                ui.notify("Заполните оба поля", color="warning")
                return

            ok, res = create_user(username, password)
            if ok:
                ui.notify("Регистрация успешна", color="positive")
                ui.navigate.to("/profile")
            else:
                ui.notify(f"Ошибка регистрации: {res}", color="negative")

        ui.button("Создать аккаунт", on_click=handle_register).classes("w-full mb-2")
        ui.button("Назад к входу", on_click=lambda: ui.navigate.to("/")).props("flat unelevated no-caps").classes(
        "mx-auto bg-transparent shadow-none border-none text-blue-600 hover:underline"
        )
