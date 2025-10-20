from typing import Optional

from nicegui import Client, ui

from backend.auth import confirm_two_factor, disable_two_factor, initiate_two_factor_setup
from backend.db import SessionLocal
from backend.models import User


def _load_user(user_id: int) -> Optional[User]:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def _update_email(user_id: int, email: str) -> bool:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.email = email or None
        db.commit()
        return True
    finally:
        db.close()


@ui.page("/profile")
async def profile_page(client: Client):
    import asyncio

    await asyncio.sleep(0.1)

    params = client.request.query_params if client and client.request else {}
    try:
        user_id = int(params.get("user_id", "0"))
    except (TypeError, ValueError):
        user_id = 0

    user = _load_user(user_id)
    if not user:
        with ui.card().classes("max-w-md mx-auto mt-20 p-6"):
            ui.label("User not found").classes("text-xl font-semibold mb-2")
            ui.button("Back to login", on_click=lambda: ui.navigate.to("/")).classes("w-full")
        return

    with ui.card().classes("max-w-3xl mx-auto mt-10 p-6 shadow-lg flex flex-col gap-4"):
        ui.label("Profile").classes("text-3xl font-bold text-center")

        with ui.row().classes("justify-between w-full"):
            ui.label(f"Username: {user.username}").classes("text-lg")
            ui.label(f"Joined: {user.created_at:%d.%m.%Y}").classes("text-lg text-gray-600")

        with ui.row().classes("justify-between w-full"):
            ui.label(f"Email: {user.email or 'not set'}").classes("text-lg")
            ui.label(
                "Last login: " + (user.last_login_at.strftime("%d.%m.%Y %H:%M") if user.last_login_at else "never")
            ).classes("text-lg text-gray-600")

        ui.separator()

        with ui.expansion("Edit email", icon="mail_outline").classes("w-full"):
            email_input = ui.input("Email", value=user.email or "").classes("w-full")

            def save_email():
                new_email = (email_input.value or "").strip()
                if _update_email(user_id, new_email):
                    ui.notify("Email updated", color="positive")
                    ui.navigate.reload()
                else:
                    ui.notify("Unable to update email", color="negative")

            ui.button("Save", on_click=save_email).classes("mt-2 bg-blue-500 text-white")

        with ui.expansion("Two-factor authentication", icon="verified_user").classes("w-full"):
            ui.label(
                "Status: enabled" if user.is_2fa_enabled else "Status: disabled"
            ).classes("text-lg mb-2")

            if user.is_2fa_enabled:

                def disable():
                    ok, message = disable_two_factor(user_id)
                    if ok:
                        ui.notify(message, color="positive")
                        ui.navigate.reload()
                    else:
                        ui.notify(message, color="negative")

                ui.button("Disable 2FA", on_click=disable).classes("bg-red-500 text-white")
            else:
                secret_container = ui.column().classes("gap-2")

                def start_setup():
                    ok, payload = initiate_two_factor_setup(user_id)
                    if not ok:
                        ui.notify(str(payload), color="negative")
                        return

                    secret_container.clear()
                    secret = payload["secret"]
                    uri = payload["otpauth_uri"]

                    with secret_container:
                        ui.label(f"Secret: {secret}").classes("font-mono text-sm bg-gray-100 p-2 rounded")
                        ui.qrcode(uri).classes("self-center")
                        code_input = ui.input("Enter verification code").classes("w-full")

                        def confirm():
                            ok_confirm, message = confirm_two_factor(user_id, code_input.value or "")
                            if ok_confirm:
                                ui.notify(message, color="positive")
                                ui.navigate.reload()
                            else:
                                ui.notify(message, color="negative")

                        ui.button("Confirm", on_click=confirm).classes("bg-green-500 text-white")

                ui.button("Enable 2FA", on_click=start_setup).classes("bg-blue-500 text-white")

        with ui.row().classes("w-full justify-between mt-4"):
            ui.button("Go to dashboard", on_click=lambda: ui.navigate.to(f"/dashboard?user_id={user_id}"))
            ui.button("Manage credentials", on_click=lambda: ui.navigate.to(f"/keys?user_id={user_id}"))
            ui.button("Sign out", on_click=lambda: ui.navigate.to("/")).classes("bg-red-500 text-white")
