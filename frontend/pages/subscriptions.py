from typing import Optional

from nicegui import Client, ui

PLANS = [
    {
        "title": "Starter",
        "price": "19 $/мес",
        "description": "До 50 зашифрованных записей, персональная поддержка и базовая аналитика.",
        "button": "Купить Starter",
    },
    {
        "title": "Professional",
        "price": "49 $/мес",
        "description": "Командный доступ (до 5 пользователей), совместный дашборд и контроль изменений.",
        "button": "Купить Professional",
    },
    {
        "title": "Enterprise",
        "price": "149 $/мес",
        "description": "SLA 24/7, безлимитные хранилища, отдельный менеджер и SSO интеграции.",
        "button": "Купить Enterprise",
    },
]


def _dashboard_url(user_id: Optional[str]) -> str:
    if user_id:
        return f"/dashboard?user_id={user_id}"
    return "/dashboard"


def _checkout_url(plan_title: str, user_id: Optional[str]) -> str:
    base = f"/checkout?plan={plan_title}"
    if user_id:
        base += f"&user_id={user_id}"
    return base


@ui.page("/subscriptions")
def subscriptions_page(client: Client):
    params = client.request.query_params if client and client.request else {}
    user_id = params.get("user_id")

    with ui.element("div").classes("bg-gray-100 min-h-screen w-full"):
        with ui.column().classes("max-w-6xl mx-auto py-16 gap-10 items-center"):
            ui.label("Выберите подписку").classes("text-4xl font-semibold text-gray-900 text-center")
            ui.label(
                "Покажите инвесторам линейку монетизации: развитие от личного сейфа до корпоративной платформы."
            ).classes("text-base text-gray-600 text-center max-w-3xl")
            with ui.row().classes("w-full gap-6 flex-wrap justify-center"):
                for plan in PLANS:
                    with ui.card().classes(
                        "w-80 p-6 bg-white shadow-lg border border-gray-200 rounded-2xl flex flex-col gap-4"
                    ):
                        ui.label(plan["title"]).classes("text-2xl font-semibold text-gray-900")
                        ui.label(plan["price"]).classes("text-lg font-medium text-blue-600")
                        ui.separator()
                        ui.label(plan["description"]).classes("text-sm leading-relaxed text-gray-600")

                        ui.button(
                            plan["button"],
                            on_click=lambda title=plan["title"]: ui.navigate.to(_checkout_url(title, user_id)),
                        ).classes("bg-blue-500 hover:bg-blue-600 text-white mt-auto w-full")
            ui.button(
                "Вернуться в дашборд",
                on_click=lambda: ui.navigate.to(_dashboard_url(user_id)),
            ).props("outline").classes("mt-8 text-blue-600 border-blue-500")
