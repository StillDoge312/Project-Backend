from typing import Optional

from nicegui import Client, ui

from backend import credentials as credential_service
from backend.db import SessionLocal
from backend.models import User


def _load_user(user_id: int) -> Optional[User]:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


@ui.page("/keys")
def keys_page(client: Client):
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

    state = {"records": []}
    focus_id = params.get("focus_id")

    header_card = ui.card().classes("max-w-4xl mx-auto mt-10 p-6 shadow-lg gap-4")
    with header_card:
        ui.label("Credentials").classes("text-3xl font-bold")
        ui.label("Securely store logins, keys and passwords. Passwords are encrypted at rest.").classes(
            "text-sm text-gray-600"
        )
        with ui.row().classes("gap-2"):
            add_button = ui.button("Add credential").classes("bg-green-500 text-white")
            ui.button("Back to dashboard", on_click=lambda: ui.navigate.to(f"/dashboard?user_id={user_id}"))
            ui.button("Profile", on_click=lambda: ui.navigate.to(f"/profile?user_id={user_id}"))

    table_container = ui.column().classes("max-w-4xl mx-auto mt-4 gap-3")

    create_dialog = ui.dialog()
    with create_dialog, ui.card().classes("w-96 p-4 gap-3"):
        ui.label("Add credential").classes("text-xl font-semibold")
        create_title = ui.input("Title").classes("w-full")
        create_login = ui.input("Login (optional)").classes("w-full")
        create_password = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
        create_notes = ui.textarea("Notes (optional)").classes("w-full")

        def submit_create():
            ok, res = credential_service.create_credential(
                user_id,
                create_title.value or "",
                create_password.value or "",
                login=create_login.value or None,
                notes=create_notes.value or None,
            )
            if ok:
                ui.notify("Credential created", color="positive")
                create_dialog.close()
                refresh(force=True)
            else:
                ui.notify(str(res), color="negative")

        ui.button("Save", on_click=submit_create).classes("bg-green-500 text-white")
        ui.button("Cancel", on_click=create_dialog.close).props("flat")

    edit_dialog = ui.dialog()
    with edit_dialog, ui.card().classes("w-96 p-4 gap-3"):
        ui.label("Update credential").classes("text-xl font-semibold")
        edit_title = ui.input("Title").classes("w-full")
        edit_login = ui.input("Login").classes("w-full")
        edit_password = ui.input("New password", password=True, password_toggle_button=True).classes("w-full")
        edit_notes = ui.textarea("Notes").classes("w-full")
        current_edit = {"id": None}

        def submit_edit():
            if current_edit["id"] is None:
                return
            ok, res = credential_service.update_credential(
                user_id,
                current_edit["id"],
                title=edit_title.value,
                login=edit_login.value,
                password=edit_password.value or None,
                notes=edit_notes.value,
            )
            if ok:
                ui.notify("Credential updated", color="positive")
                edit_dialog.close()
                refresh(force=True)
            else:
                ui.notify(str(res), color="negative")

        ui.button("Save", on_click=submit_edit).classes("bg-blue-500 text-white")
        ui.button("Cancel", on_click=edit_dialog.close).props("flat")

    def render_records():
        table_container.clear()
        if not state["records"]:
            with table_container:
                ui.label("No credentials stored yet").classes("text-gray-600 italic text-center")
            return

        for record in state["records"]:
            is_focus = focus_id and str(record["id"]) == focus_id
            with table_container:
                with ui.card().classes(
                    "p-4 border gap-3" + (" bg-blue-50" if is_focus else "")
                ):
                    ui.label(record["title"]).classes("text-lg font-semibold")
                    if record.get("login"):
                        ui.label(f"Login: {record['login']}").classes("text-sm text-gray-600")
                    if record.get("notes"):
                        ui.label(record["notes"]).classes("text-sm text-gray-500")

                    with ui.row().classes("gap-2"):
                        def copy_password(value: str):
                            ui.run_javascript(f"navigator.clipboard.writeText('{value}')")
                            ui.notify("Password copied", color="info")

                        ui.button("Copy", on_click=lambda v=record["password"]: copy_password(v)).props("outline")

                        def open_edit():
                            current_edit["id"] = record["id"]
                            edit_title.value = record["title"]
                            edit_login.value = record.get("login") or ""
                            edit_notes.value = record.get("notes") or ""
                            edit_password.value = ""
                            edit_dialog.open()

                        ui.button("Edit", on_click=open_edit).props("outline")

                        def delete_record():
                            ok, message = credential_service.delete_credential(user_id, record["id"])
                            if ok:
                                ui.notify(message, color="positive")
                                refresh(force=True)
                            else:
                                ui.notify(message, color="negative")

                        ui.button("Delete", on_click=delete_record, color="red").props("outline")

    def refresh(force: bool = False):
        if force or not state["records"]:
            state["records"] = credential_service.list_credentials(user_id, include_sensitive=True)
        render_records()

    add_button.on_click(create_dialog.open)

    refresh(force=True)
