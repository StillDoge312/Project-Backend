# frontend/pages/profile.py
from nicegui import ui

@ui.page("/profile")
def profile_page():
    with ui.card().classes("w-80 mx-auto mt-20 p-6 shadow-lg"):
        ui.label("Профиль").classes("text-2xl mb-4")

        ui.label("Добро пожаловать в личный кабинет!").classes("mb-4")

        # Кнопка выхода — просто редирект на страницу логина
        ui.button("Выйти", on_click=lambda: ui.navigate.to("/")).classes("w-full outlined")
