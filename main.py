import os
from nicegui import ui, app
from backend import api
from backend.db import engine, Base

os.makedirs("data", exist_ok=True)


Base.metadata.create_all(bind=engine)


app.include_router(api.router)

import frontend.pages.login
import frontend.pages.register
import frontend.pages.profile


from backend.auth import create_user
create_user("admin", "1234")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8000, reload=True)
# теперь доступно по адресу http://localhost:8000