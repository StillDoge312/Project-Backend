from nicegui import ui

from backend.db import run_migrations


def bootstrap_database() -> bool:
    try:
        run_migrations()
        print("Database migrated successfully")
        return True
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to run migrations: {exc}")
        return False


if bootstrap_database():
    from frontend.pages import dashboard, keys, login, profile, register, subscriptions, checkout  # noqa: F401

    ui.run(host="0.0.0.0", port=8000, reload=False)
else:
    print("Application terminated due to migration error")
