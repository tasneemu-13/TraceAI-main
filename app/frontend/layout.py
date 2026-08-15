from nicegui import ui, app

def theme_setup():
    """
    Sets up the dark theme, google fonts, custom styling sheet, and mesh gradient background.
    """
    ui.dark_mode().enable()
    # Inject Google Fonts and Custom CSS
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Playfair+Display:ital,wght@0,700;1,700&display=swap" rel="stylesheet">')
    ui.add_head_html('<link rel="stylesheet" href="/static/custom.css">')
    
    # Animated Mesh background
    ui.html('<div class="mesh-bg"></div>')

def header_nav():
    """
    Renders the responsive sticky glassmorphism navbar.
    """
    # Read user session data from NiceGUI's client-local storage
    user = app.storage.user.get("user")
    role = app.storage.user.get("role")
    
    with ui.header().classes("glass-nav q-py-sm q-px-md row items-center justify-between text-white"):
        # Logo with typing-like border highlight
        with ui.row().classes("items-center cursor-pointer").on("click", lambda: ui.navigate.to("/")):
            ui.icon("radar", size="2.2rem").classes("text-blue-500 q-mr-xs animate-pulse")
            ui.label("TraceAI").classes("text-h5 text-weight-bold tracking-wider")
            ui.label("Finding Hope Through Intelligence").classes("text-caption text-blue-300 q-ml-sm gt-sm")
            
        with ui.row().classes("items-center q-gutter-md"):
            if user:
                # User logged in - Role specific navigation only
                def logout():
                    app.storage.user.clear()
                    ui.notify("Logged out successfully", type="info")
                    ui.navigate.to("/")
                
                if role == "Admin":
                    ui.button("Admin Panel", on_click=lambda: ui.navigate.to("/admin")).classes("glass-btn")
                elif role == "Officer":
                    ui.button("Officer Dashboard", on_click=lambda: ui.navigate.to("/officer")).classes("glass-btn")
                
                with ui.row().classes("items-center q-ml-sm"):
                    ui.icon("account_circle", size="1.8rem").classes("text-blue-400")
                    ui.label(f"{user} ({role})").classes("text-subtitle2 q-mr-sm")
                    ui.button(icon="logout", on_click=logout).classes("glass-btn").tooltip("Logout")
            else:
                # Public visitor - Default Home Page header
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).classes("glass-btn")
                ui.button("Public Sighting", on_click=lambda: ui.navigate.to("/public")).classes("glass-btn")
                ui.button("Portal Login", on_click=lambda: ui.navigate.to("/login")).classes("glass-btn text-blue-400")
                ui.button("Android App", on_click=lambda: ui.navigate.to("/mobile")).classes("glass-btn text-teal-400 gt-xs")
