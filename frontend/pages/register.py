from nicegui import ui

def page(ui):
    @ui.page("/register")
    def register_page():
        with ui.card().classes("w-80 mx-auto mt-20 p-6 shadow-lg"):
            ui.label("Регистрация").classes("text-2xl mb-4")

            username = ui.input("Логин").classes("w-full mb-2")
            password = ui.input("Пароль", password=True, password_toggle_button=True).classes("w-full mb-2")

            def handle_register():
                print("Register:", username.value, "Password:", password.value)
                ui.notify("Пользователь зарегистрирован (пока фейк)")

            ui.button("Создать аккаунт", on_click=handle_register).classes("w-full")
