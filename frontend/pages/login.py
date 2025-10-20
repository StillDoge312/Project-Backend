from nicegui import ui

from backend.auth import verify_user


@ui.page("/")
def login_page():
    pending_credentials = {"username": None, "password": None}

    with ui.card().classes("w-96 mx-auto mt-20 p-6 shadow-lg flex flex-col gap-3"):
        ui.label("Sign in").classes("text-2xl font-semibold text-center mb-2")

        username_input = ui.input("Username").classes("w-full")
        password_input = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

        otp_dialog = ui.dialog()
        with otp_dialog, ui.card().classes("w-80 p-4 gap-3"):
            ui.label("Two-factor authentication").classes("text-lg font-semibold")
            otp_input = ui.input("One-time code").classes("w-full")

            def submit_otp():
                code = (otp_input.value or "").strip()
                if not code:
                    ui.notify("Enter the 2FA code", color="warning")
                    return

                ok, res = verify_user(
                    pending_credentials["username"],
                    pending_credentials["password"],
                    otp_code=code,
                )
                if ok:
                    otp_dialog.close()
                    ui.notify("Login successful", color="positive")
                    ui.navigate.to(f"/profile?user_id={res['user_id']}")
                else:
                    if isinstance(res, dict) and res.get("code") == "2fa_required":
                        ui.notify("Please enter the verification code", color="warning")
                    else:
                        ui.notify(str(res), color="negative")

            ui.button("Verify", on_click=submit_otp).classes("w-full bg-blue-500 text-white")
            ui.button("Cancel", on_click=otp_dialog.close).props("flat")

        def open_two_factor(user_id: int):
            pending_credentials["user_id"] = user_id
            otp_input.value = ""
            otp_dialog.open()

        def handle_login():
            username = (username_input.value or "").strip()
            password = password_input.value or ""

            if not username or not password:
                ui.notify("Username and password are required", color="warning")
                return

            ok, res = verify_user(username, password)
            if ok:
                ui.notify("Login successful", color="positive")
                ui.navigate.to(f"/profile?user_id={res['user_id']}")
                return

            if isinstance(res, dict) and res.get("code") == "2fa_required":
                pending_credentials["username"] = username
                pending_credentials["password"] = password
                open_two_factor(res["user_id"])
                return

            ui.notify(str(res), color="negative")

        ui.button("Log in", on_click=handle_login).classes("w-full bg-blue-500 text-white")
        ui.button(
            "Create account",
            on_click=lambda: ui.navigate.to("/register"),
        ).props("flat unelevated no-caps").classes(
            "mx-auto text-blue-600 hover:underline"
        )
