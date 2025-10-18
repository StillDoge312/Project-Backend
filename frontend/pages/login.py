# frontend/pages/login.py
from nicegui import ui
from backend.auth import verify_user

@ui.page("/")
def login_page():
    with ui.card().classes(
        "w-80 mx-auto mt-20 p-6 shadow-lg"
        ):
        ui.label("Вход").classes("text-2xl mb-4")

        username_input = ui.input("Логин").classes("w-full mb-2")
        password_input = ui.input("Пароль", password=True, password_toggle_button=True).classes(
            "w-full mb-2"
            )

        def try_login():
            username = (username_input.value or "").strip()
            password = password_input.value or ""
            if not username or not password:
                ui.notify("Заполните оба поля", color="warning")
                return

            ok, res = verify_user(username, password)
            if ok:
                ui.notify("Успешный вход", color="positive")
<<<<<<< HEAD
                ui.navigate.to(f"/profile?user_id={user_id}")
=======
                ui.navigate.to("/profile")
>>>>>>> parent of eeb9efe (New Reworked system)
            else:
                ui.notify(f"Ошибка: {res}", color="negative")

        ui.button("Войти", on_click=try_login).classes("w-full mb-2")
<<<<<<< HEAD
        ui.button("Регистрация", on_click=lambda: ui.navigate.to("/register")).props("flat unelevated no-caps").classes(
            "mx-auto bg-transparent shadow-none border-none text-blue-600 hover:underline"
        )
=======
        ui.button("Регистрация",on_click=lambda: ui.navigate.to("/register")).props("flat unelevated no-caps").classes(
        "mx-auto bg-transparent shadow-none border-none text-blue-600 hover:underline"
        )
>>>>>>> parent of eeb9efe (New Reworked system)
