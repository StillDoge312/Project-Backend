from nicegui import ui, app
from backend import api
import frontend.ui as frontend_ui

fastapi_app = app  

fastapi_app.include_router(api.router)

frontend_ui.setup_ui(ui, fastapi_app)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
