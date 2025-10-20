import json
from datetime import datetime
from typing import Dict, List, Optional

from nicegui import Client, ui
from sqlalchemy.exc import SQLAlchemyError

from backend import credentials as credential_service
from backend.auth import (
    confirm_two_factor,
    disable_two_factor,
    initiate_two_factor_setup,
    set_master_key,
    verify_master_key,
)
from backend.db import SessionLocal
from backend.models import Key, User


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


def _list_keys(user_id: int) -> List[Key]:
    db = SessionLocal()
    try:
        return (
            db.query(Key)
            .filter(Key.user_id == user_id)
            .order_by(Key.created_at.desc())
            .all()
        )
    finally:
        db.close()


def _create_key(user_id: int, name: str, value: str, description: str = ""):
    db = SessionLocal()
    try:
        if not name.strip():
            return False, "Enter key name"
        if not value.strip():
            return False, "Enter key value"
        key = Key(
            user_id=user_id,
            key_name=name.strip(),
            key_value=value.strip(),
            description=description.strip() or None,
            created_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(key)
        db.commit()
        db.refresh(key)
        return True, key
    except SQLAlchemyError as exc:
        db.rollback()
        return False, f"Database error: {exc}"
    finally:
        db.close()


def _toggle_key_active(key_id: int, value: bool) -> bool:
    db = SessionLocal()
    try:
        key = db.query(Key).filter(Key.id == key_id).first()
        if not key:
            return False
        key.is_active = value
        db.commit()
        return True
    finally:
        db.close()


def _delete_key(key_id: int) -> bool:
    db = SessionLocal()
    try:
        key = db.query(Key).filter(Key.id == key_id).first()
        if not key:
            return False
        db.delete(key)
        db.commit()
        return True
    finally:
        db.close()


def _stat_card(title: str, value, description: str):
    with ui.card().classes("min-w-[220px] flex-1 p-4 bg-blue-50 shadow-sm"):
        ui.label(title).classes("text-xs uppercase tracking-wide text-gray-600")
        ui.label(str(value)).classes("text-3xl font-semibold text-gray-900")
        ui.label(description).classes("text-xs text-gray-500")


def _activity_item(icon: str, title: str, subtitle: str):
    with ui.row().classes("items-start gap-3"):
        ui.icon(icon).classes("text-blue-500 mt-1")
        with ui.column().classes("gap-1"):
            ui.label(title).classes("text-sm font-medium text-gray-800")
            ui.label(subtitle).classes("text-xs text-gray-600")


def _render_overview(content_area: ui.element, user: User):
    credential_count = len(credential_service.list_credentials(user.id))
    key_count = len(_list_keys(user.id))

    with content_area:
        with ui.column().classes("w-full gap-6"):
            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-3"):
                ui.label("Dashboard").classes("text-2xl font-semibold")
                ui.label("Overview and quick actions.").classes("text-sm text-gray-600")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    _stat_card("Stored credentials", credential_count, "Passwords and secrets")
                    _stat_card("Active keys", key_count, "API access tokens")
                    status = "Enabled" if user.is_2fa_enabled else "Disabled"
                    _stat_card("2FA", status, "Two-factor authentication")
                with ui.row().classes("w-full gap-2 flex-wrap"):
                    ui.button(
                        "Add password",
                        icon="password",
                        on_click=lambda: ui.emit("navigate:passwords"),
                    ).classes("bg-blue-500 text-white")
                    ui.button(
                        "Add key",
                        icon="vpn_key",
                        on_click=lambda: ui.emit("navigate:keys"),
                    ).classes("bg-blue-500 text-white")
                    ui.button(
                        "Купить подписку",
                        icon="shopping_cart",
                        on_click=lambda: ui.navigate.to(f"/subscriptions?user_id={user.id}"),
                    ).classes("bg-blue-500 text-white")
                    ui.button(
                        "Open profile",
                        icon="person",
                        on_click=lambda: ui.emit("navigate:profile"),
                    ).props("outline")

            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Recent activity").classes("text-xl font-semibold")
                if credential_count or key_count:
                    with ui.column().classes("gap-3"):
                        if credential_count:
                            _activity_item(
                                "password",
                                "Passwords updated",
                                'Open the "Passwords" view to manage stored records.',
                            )
                        if key_count:
                            _activity_item(
                                "vpn_key",
                                "Access keys updated",
                                'Review keys in the "Keys" section.',
                            )
                else:
                    ui.label("Activity will appear here after you add passwords or keys.").classes(
                        "text-sm text-gray-600"
                    )


def _render_profile(content_area: ui.element, user: User, refresh_cb):
    with content_area:
        with ui.column().classes("w-full gap-6"):
            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Profile").classes("text-2xl font-semibold")
                with ui.row().classes("items-center gap-6 flex-wrap"):
                    ui.avatar(icon="person").props("size=72").classes("bg-blue-100 text-blue-600")
                    with ui.column().classes("gap-1"):
                        ui.label(user.username).classes("text-xl font-semibold")
                        ui.label(user.email or "Email not set").classes("text-sm text-gray-600")
                        ui.label(f"Joined: {user.created_at:%d.%m.%Y}").classes("text-xs text-gray-500")
                        if user.last_login_at:
                            ui.label(f"Last login: {user.last_login_at:%d.%m.%Y %H:%M}").classes(
                                "text-xs text-gray-500"
                            )

            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-3"):
                ui.label("Contact information").classes("text-xl font-semibold")
                ui.label("Update email to receive notifications and recovery links.").classes(
                    "text-sm text-gray-600"
                )
                email_input = ui.input("Email", value=user.email or "").props("outlined").classes("w-full")

                def save_email():
                    new_email = (email_input.value or "").strip()
                    if _update_email(user.id, new_email):
                        ui.notify("Email updated", color="positive")
                        refresh_cb()
                    else:
                        ui.notify("Unable to update email", color="negative")

                ui.button("Save", on_click=save_email, icon="save").classes("self-start bg-blue-500 text-white")

            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-3"):
                ui.label("Quick stats").classes("text-xl font-semibold")
                stats = credential_service.list_credentials(user.id)
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    _stat_card("Credentials", len(stats), "Saved passwords and notes")
                    status = "Enabled" if user.is_2fa_enabled else "Disabled"
                    _stat_card("2FA", status, "Account protection")
                    _stat_card("Master key", "Yes" if user.master_key else "No", "Sensitive actions")


def _render_keys(content_area: ui.element, user: User):
    state: Dict[str, List[Key]] = {"records": _list_keys(user.id)}

    with content_area:
        with ui.column().classes("w-full gap-6"):
            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Access keys").classes("text-2xl font-semibold")
                ui.label("Generate and manage API keys.").classes("text-sm text-gray-600")

                key_name = ui.input("Key name").props("outlined").classes("w-full")
                key_value = ui.input("Key value", password=True, password_toggle_button=True).props("outlined").classes("w-full")
                key_description = ui.textarea("Description (optional)").props("outlined").classes("w-full")

                def add_key():
                    ok, result = _create_key(
                        user.id,
                        key_name.value or "",
                        key_value.value or "",
                        description=key_description.value or "",
                    )
                    if ok:
                        ui.notify("Key added", color="positive")
                        key_name.value = ""
                        key_value.value = ""
                        key_description.value = ""
                        state["records"] = _list_keys(user.id)
                        render_list()
                    else:
                        ui.notify(str(result), color="negative")

                ui.button("Save key", on_click=add_key, icon="add").classes("self-start bg-blue-500 text-white")

            list_container = ui.column().classes("w-full gap-3")

            def render_list():
                list_container.clear()
                if not state["records"]:
                    with list_container:
                        with ui.card().classes("w-full p-6 bg-white shadow-sm"):
                            ui.label("No keys yet").classes("text-sm text-gray-600")
                    return

                for key in state["records"]:
                    with list_container:
                        with ui.card().classes("w-full p-4 bg-white shadow-sm"):
                            with ui.row().classes("w-full justify-between items-start flex-wrap gap-4"):
                                with ui.column().classes("gap-1"):
                                    ui.label(key.key_name).classes("text-lg font-semibold")
                                    if key.description:
                                        ui.label(key.description).classes("text-sm text-gray-600")
                                    ui.label(f"Created: {key.created_at:%d.%m.%Y %H:%M}").classes("text-xs text-gray-500")
                                with ui.row().classes("items-center gap-2"):
                                    masked = "••••" + key.key_value[-4:]
                                    ui.label(masked).classes("font-mono text-sm bg-gray-100 px-2 py-1 rounded")

                                    def copy_value(value: str = key.key_value):
                                        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(value)})")
                                        ui.notify("Key copied", color="info")

                                    ui.button(icon="content_copy", on_click=copy_value).props("flat")

                                    def toggle_key(active: bool, key_id: int = key.id):
                                        if _toggle_key_active(key_id, active):
                                            ui.notify("Status updated", color="positive")
                                            state["records"] = _list_keys(user.id)
                                            render_list()
                                        else:
                                            ui.notify("Unable to update status", color="negative")

                                    ui.switch(
                                        "Active",
                                        value=key.is_active,
                                        on_change=lambda e, key_id=key.id: toggle_key(e.value, key_id),
                                    )

                                    def remove(key_id: int = key.id):
                                        if _delete_key(key_id):
                                            ui.notify("Key removed", color="positive")
                                            state["records"] = _list_keys(user.id)
                                            render_list()
                                        else:
                                            ui.notify("Unable to remove key", color="negative")

                                    ui.button(icon="delete", color="red", on_click=remove).props("flat")

            render_list()


def _render_passwords(content_area: ui.element, user: User):
    state: Dict[str, List[dict]] = {
        "records": credential_service.list_credentials(user.id, include_sensitive=True)
    }

    with content_area:
        with ui.column().classes("w-full gap-6"):
            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Passwords and logins").classes("text-2xl font-semibold")
                ui.label("Securely store credentials and private notes.").classes("text-sm text-gray-600")

                title_input = ui.input("Title").props("outlined").classes("w-full")
                login_input = ui.input("Login (optional)").props("outlined").classes("w-full")
                password_input = ui.input("Password", password=True, password_toggle_button=True).props("outlined").classes("w-full")
                notes_input = ui.textarea("Notes (optional)").props("outlined").classes("w-full")

                def add_record():
                    ok, result = credential_service.create_credential(
                        user.id,
                        title_input.value or "",
                        password_input.value or "",
                        login=login_input.value or None,
                        notes=notes_input.value or None,
                    )
                    if ok:
                        ui.notify("Credential saved", color="positive")
                        title_input.value = ""
                        login_input.value = ""
                        password_input.value = ""
                        notes_input.value = ""
                        state["records"] = credential_service.list_credentials(user.id, include_sensitive=True)
                        render_list()
                    else:
                        ui.notify(str(result), color="negative")

                ui.button("Save credential", on_click=add_record, icon="add").classes(
                    "self-start bg-blue-500 text-white"
                )

            list_container = ui.column().classes("w-full gap-3")

            def render_list():
                list_container.clear()
                if not state["records"]:
                    with list_container:
                        with ui.card().classes("w-full p-6 bg-white shadow-sm"):
                            ui.label("No credentials yet").classes("text-sm text-gray-600")
                    return

                for record in state["records"]:
                    with list_container:
                        with ui.card().classes("w-full p-4 bg-white shadow-sm"):
                            with ui.row().classes("w-full justify-between items-start flex-wrap gap-4"):
                                with ui.column().classes("gap-1"):
                                    ui.label(record["title"]).classes("text-lg font-semibold")
                                    if record.get("login"):
                                        ui.label(f"Login: {record['login']}").classes("text-sm text-gray-600")
                                    if record.get("notes"):
                                        ui.label(record["notes"]).classes("text-sm text-gray-500")
                                    ui.label(f"Created: {record['created_at']:%d.%m.%Y %H:%M}").classes("text-xs text-gray-500")
                                with ui.row().classes("items-center gap-2"):
                                    def copy_password(value: str = record["password"]):
                                        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(value)})")
                                        ui.notify("Password copied", color="info")

                                    ui.button(icon="content_copy", on_click=copy_password).props("flat")

                                    def delete_record(rec_id: int = record["id"]):
                                        ok, message = credential_service.delete_credential(user.id, rec_id)
                                        if ok:
                                            ui.notify("Credential removed", color="positive")
                                            state["records"] = credential_service.list_credentials(
                                                user.id, include_sensitive=True
                                            )
                                            render_list()
                                        else:
                                            ui.notify(message, color="negative")

                                    ui.button(icon="delete", color="red", on_click=delete_record).props("flat")

            render_list()


def _render_settings(content_area: ui.element, user: User, refresh_cb):
    with content_area:
        with ui.column().classes("w-full gap-6"):
            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Two-factor authentication").classes("text-2xl font-semibold")
                ui.label("Add one-time codes for additional protection.").classes("text-sm text-gray-600")

                secret_container = ui.column().classes("w-full gap-3")

                if user.is_2fa_enabled:

                    def disable():
                        ok, message = disable_two_factor(user.id)
                        if ok:
                            ui.notify(message, color="positive")
                            refresh_cb()
                        else:
                            ui.notify(message, color="negative")

                    ui.label("Status: enabled").classes("text-sm text-green-600")
                    ui.button("Disable 2FA", on_click=disable, icon="lock_open").classes(
                        "self-start bg-red-500 text-white"
                    )
                else:

                    def start_setup():
                        ok, payload = initiate_two_factor_setup(user.id)
                        if not ok:
                            ui.notify(str(payload), color="negative")
                            return
                        secret_container.clear()
                        secret = payload["secret"]
                        uri = payload["otpauth_uri"]
                        with secret_container:
                            ui.label(f"Secret: {secret}").classes(
                                "font-mono text-sm bg-gray-100 px-3 py-2 rounded"
                            )
                            ui.code(uri, language="text").classes("self-start bg-gray-900 text-white w-full max-w-xs")
                            code_input = ui.input("Enter one-time code").props("outlined").classes(
                                "w-full max-w-sm"
                            )

                            def confirm():
                                ok_confirm, message = confirm_two_factor(user.id, code_input.value or "")
                                if ok_confirm:
                                    ui.notify(message, color="positive")
                                    refresh_cb()
                                else:
                                    ui.notify(message, color="negative")

                            ui.button("Confirm", on_click=confirm, icon="check").classes(
                                "self-start bg-green-500 text-white"
                            )

                    ui.label("Status: disabled").classes("text-sm text-gray-600")
                    ui.button("Enable 2FA", on_click=start_setup, icon="lock").classes(
                        "self-start bg-blue-500 text-white"
                    )

                secret_container

            with ui.card().classes("w-full p-6 bg-white shadow-sm flex flex-col gap-4"):
                ui.label("Master key").classes("text-2xl font-semibold")
                ui.label("Use a master key to confirm sensitive actions.").classes("text-sm text-gray-600")

                current_input = ui.input(
                    "Current master key", password=True, password_toggle_button=True
                ).props("outlined").classes("w-full max-w-sm")
                if not user.master_key:
                    current_input.classes("hidden")

                new_input = ui.input(
                    "New master key", password=True, password_toggle_button=True
                ).props("outlined").classes("w-full max-w-sm")
                confirm_input = ui.input(
                    "Confirm master key", password=True, password_toggle_button=True
                ).props("outlined").classes("w-full max-w-sm")

                def save_master_key():
                    new_value = new_input.value or ""
                    confirm_value = confirm_input.value or ""
                    if new_value != confirm_value:
                        ui.notify("Values do not match", color="warning")
                        return
                    if user.master_key and not verify_master_key(user.id, current_input.value or ""):
                        ui.notify("Current master key is incorrect", color="negative")
                        return
                    ok, message = set_master_key(user.id, new_value)
                    if ok:
                        ui.notify(message, color="positive")
                        refresh_cb()
                    else:
                        ui.notify(message, color="negative")

                ui.button("Save", on_click=save_master_key, icon="save").classes(
                    "self-start bg-blue-500 text-white"
                )


@ui.page("/dashboard")
def dashboard_page(client: Client):
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

    active_view = {"value": "dashboard"}
    nav_buttons: Dict[str, ui.button] = {}
    content_area_holder: Dict[str, Optional[ui.element]] = {"element": None}

    def set_active(view: str):
        active_view["value"] = view
        update_nav()
        render_content()

    def update_nav():
        base = "w-full justify-start text-left no-wrap"
        for view, button in nav_buttons.items():
            if view == active_view["value"]:
                button.classes(replace=f"{base} bg-blue-500 text-white")
            else:
                button.classes(replace=f"{base} text-gray-700 hover:bg-gray-100")

    def render_content():
        content_area = content_area_holder["element"]
        if content_area is None:
            return
        current_user = _load_user(user_id)
        if not current_user:
            content_area.clear()
            with content_area:
                ui.label("User session is no longer valid").classes("text-lg text-red-500")
            return
        content_area.clear()
        refresh_cb = render_content
        if active_view["value"] == "dashboard":
            _render_overview(content_area, current_user)
        elif active_view["value"] == "profile":
            _render_profile(content_area, current_user, refresh_cb)
        elif active_view["value"] == "keys":
            _render_keys(content_area, current_user)
        elif active_view["value"] == "passwords":
            _render_passwords(content_area, current_user)
        else:
            _render_settings(content_area, current_user, refresh_cb)

    def handle_navigation(event):
        mapping = {
            "navigate:profile": "profile",
            "navigate:keys": "keys",
            "navigate:passwords": "passwords",
        }
        target = mapping.get(event.sender)
        if target:
            set_active(target)

    ui.on("navigate:profile", handle_navigation)
    ui.on("navigate:keys", handle_navigation)
    ui.on("navigate:passwords", handle_navigation)

    with ui.column().classes("w-full min-h-screen bg-gray-100"):
        with ui.row().classes("w-full bg-gray-200 px-8 py-4 items-center justify-between shadow-sm"):
            ui.label("Key Manager").classes("text-xl font-semibold text-gray-800")
            with ui.row().classes("items-center gap-3"):
                ui.label(user.username).classes("text-sm text-gray-700")
                avatar = ui.avatar(icon="person").props("size=40 clickable")
                avatar.classes("bg-purple-100 text-purple-600 cursor-pointer")
                avatar.on("click", lambda: ui.navigate.to(f"/profile?user_id={user_id}"))

        with ui.row().classes("flex-1 w-full"):
            with ui.column().classes("w-64 bg-white border-r border-gray-200 py-6 px-4 gap-3"):
                nav_config = [
                    ("dashboard", "Dashboard", "space_dashboard"),
                    ("profile", "Profile", "person"),
                    ("keys", "Keys", "vpn_key"),
                    ("passwords", "Passwords", "password"),
                    ("settings", "Settings", "settings"),
                ]
                for view, label, icon in nav_config:
                    button = ui.button(
                        label,
                        on_click=lambda v=view: set_active(v),
                        icon=icon,
                    ).props("flat no-caps")
                    nav_buttons[view] = button
                update_nav()

            content_area_holder["element"] = ui.column().classes("flex-1 h-full overflow-auto p-8 gap-6")

    render_content()


