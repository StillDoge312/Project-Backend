from nicegui import ui

from backend.auth import create_user


@ui.page("/register")
def register_page():
    with ui.card().classes("w-96 mx-auto mt-16 p-6 shadow-lg flex flex-col gap-3"):
        ui.label("Create account").classes("text-2xl font-semibold text-center")

        username_input = ui.input("Username").props("outlined").classes("w-full")
        email_input = ui.input("Email (optional)").props("outlined").classes("w-full")
        password_input = ui.input("Password", password=True, password_toggle_button=True).props("outlined").classes("w-full")
        confirm_input = ui.input("Confirm password", password=True, password_toggle_button=True).props("outlined").classes("w-full")

        def handle_register():
            username = (username_input.value or "").strip()
            email = (email_input.value or "").strip()
            password = password_input.value or ""
            confirm = confirm_input.value or ""

            if not username or not password:
                ui.notify("Username and password are required", color="warning")
                return
            if password != confirm:
                ui.notify("Passwords do not match", color="warning")
                return

            ok, res = create_user(username, password, email=email or None)
            if ok:
                user_id = res.get("user_id") if isinstance(res, dict) else None
                ui.notify("Account created", color="positive")
                if user_id:
                    ui.navigate.to(f"/dashboard?user_id={user_id}")
                else:
                    ui.navigate.to("/")
            else:
                ui.notify(str(res), color="negative")

        ui.button("Register", on_click=handle_register).classes("w-full bg-green-500 text-white")
        ui.button("Back to login", on_click=lambda: ui.navigate.to("/")).props("flat unelevated no-caps").classes(
            "mx-auto text-blue-600 hover:underline"
        )
