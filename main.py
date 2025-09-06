from nicegui import ui

dark = ui.dark_mode()

def toggle_theme():
    dark.toggle()   

ui.label('Switch mode:')
ui.button('Переключить тему', on_click=toggle_theme)

def register():
    if username.value and password.value:
        ui.notify(f'✅ Registered!\nUser: {username.value}\nPassword: {password.value}')
    else:
        ui.notify('⚠️ Please fill in all fields!')

with ui.row().classes('w-full justify-center mt-8'):
    ui.label('Добро пожаловать! Зарегистрируйтесь ниже 👇').classes('text-2xl font-bold')

with ui.row().classes('w-full justify-center mt-8'):
    with ui.card().classes('p-8 w-96 shadow-lg'):
        ui.label('Регистрация').classes('text-xl font-semibold mb-4 text-center')

        username = ui.input('Username').classes('w-full mb-4')
        password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full mb-4')

        ui.button('Register', on_click=register).classes('w-full bg-blue-500 text-white')
        
ui.run()
