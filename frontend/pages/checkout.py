from urllib.parse import unquote

from nicegui import Client, ui


@ui.page("/checkout")
def checkout_page(client: Client):
    plan = client.request.query_params.get("plan", "") if client and client.request else ""
    plan_title = unquote(plan) if plan else "Выбранная подписка"

    with ui.element("div").classes("bg-gray-100 min-h-screen w-full"):
        with ui.column().classes("max-w-5xl mx-auto py-16 gap-10"):
            ui.label("Оформление покупки").classes("text-4xl font-semibold text-gray-900 text-center")
            if plan:
                with ui.card().classes("mx-auto w-full max-w-xl p-6 bg-white shadow-md border border-gray-200 rounded-2xl"):
                    ui.label(plan_title).classes("text-2xl font-semibold text-gray-900")
                    ui.label(
                        "Оплатите подписку и сразу покажите инвесторам сценарий онбординга клиента."
                    ).classes("text-sm text-gray-600")
            with ui.card().classes(
                "w-full max-w-xl mx-auto p-8 bg-white shadow-lg border border-gray-200 rounded-2xl flex flex-col gap-5"
            ):
                name_input = ui.input("Имя").props("outlined").classes("w-full")
                email_input = ui.input("Email").props("outlined").classes("w-full")
                card_number_input = ui.input("Номер карты").props("outlined").classes("w-full")
                expiry_input = ui.input("Срок действия (MM/YY)").props("outlined").classes("w-full")
                cvc_input = ui.input("CVC", password=True, password_toggle_button=True).props("outlined").classes("w-full")

                def submit_payment():
                    if not all([
                        name_input.value,
                        email_input.value,
                        card_number_input.value,
                        expiry_input.value,
                        cvc_input.value,
                    ]):
                        ui.notify("Заполните все поля", color="warning")
                        return
                    ui.notify("Оплата успешна", color="positive")
                    ui.navigate.to("/dashboard")

                ui.button("Оплатить", on_click=submit_payment).classes(
                    "bg-blue-500 hover:bg-blue-600 text-white w-full h-12 text-lg"
                )
            ui.button(
                "Вернуться к подпискам",
                on_click=lambda: ui.navigate.to("/subscriptions"),
            ).props("outline").classes("mx-auto text-blue-600 border-blue-500")
