from nicegui import ui

def page(ui):
    @ui.page("/")
    def login_page():
        with ui.card().classes("w-80 mx-auto mt-20 p-6 shadow-lg"):
            ui.label("Вход").classes("text-2xl mb-4")

            username = ui.input("Логин").classes("w-full mb-2")
            password = ui.input("Пароль", password=True, password_toggle_button=True).classes("w-full mb-4")

            def handle_login():
                print("Login:", username.value, "Password:", password.value)
                ui.notify("Попробуем войти...")

            ui.button("Войти", on_click=handle_login).classes("w-full")
