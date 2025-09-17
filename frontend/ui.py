from frontend.pages import login  
from frontend.pages import register
from frontend.pages import profile

def setup_ui(ui, app):
    login.page(ui)
    register.page(ui)
    profile.page(ui)