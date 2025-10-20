from nicegui import Client, ui

PLANS = [
    {
        "title": "Starter",
        "price": "19 $/мес",
        "description": "Сейф для личных записей, 50 зашифрованных ключей, базовая поддержка.",
        "button": "Купить Starter",
    },
    {
        "title": "Professional",
        "price": "49 $/мес",
        "description": "Командный доступ, до 5 участников, общий дашборд и аудит действий.",
        "button": "Купить Professional",
    },
    {
        "title": "Enterprise",
        "price": "149 $/мес",
        "description": "SLA 24/7, неограниченные хранилища, отдельный менеджер и SSO интеграции.",
        "button": "Купить Enterprise",
    },
]


@ui.page("/subscriptions")
def subscriptions_page(client: Client):
    with ui.element("div").classes("bg-gray-100 min-h-screen w-full"):
        with ui.column().classes("max-w-6xl mx-auto py-16 gap-10 items-center"):
            ui.label("Выберите подписку").classes("text-4xl font-semibold text-gray-900 text-center")
            ui.label(
                "Покажите инвесторам, как платформа масштабируется: от личного сейфа до корпоративного кластера." 
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
                            on_click=lambda p=plan["title"]: ui.navigate.to(f"/checkout?plan={p}"),
                        ).classes("bg-blue-500 hover:bg-blue-600 text-white mt-auto w-full")
            ui.button(
                "Вернуться в дашборд",
                on_click=lambda: ui.navigate.to("/dashboard"),
            ).props("outline").classes("mt-8 text-blue-600 border-blue-500")
