from nicegui import ui, app
from app.frontend import layout

def content():
    """
    Renders the premium Company Info / About TraceAI page.
    """
    layout.theme_setup()
    
    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md q-mb-xl"):
        # Top distraction-free navigation back to home
        with ui.row().classes("w-full max-w-4xl justify-start items-center q-mb-md"):
            ui.button("Back to Home", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("glass-btn text-blue-400").props("flat dense")
            
        # Header title
        ui.label("About TraceAI").classes("text-h3 text-weight-bolder text-white q-mb-xs text-center")
        ui.label("Next-generation intelligence dedicated to locating missing citizens and rebuilding lives.").classes("text-subtitle1 text-slate-400 q-mb-xl text-center")
        
        # Main Info Card
        with ui.card().classes("w-full max-w-4xl glass-card q-pa-lg text-white q-mb-lg"):
            ui.label("Our Mission").classes("text-h5 text-weight-bold text-gradient-blue-purple q-mb-sm")
            ui.label(
                "Every year, thousands of families face the distress of a missing loved one. "
                "TraceAI was founded on a simple principle: no case should go cold due to lack of tools. "
                "By bridging state-of-the-art artificial intelligence with day-to-day law enforcement operations, "
                "we provide a cinematic, highly-effective dashboard to compile sighting matches, progressive age estimates, "
                "and timeline logs dynamically in real-time."
            ).classes("text-body1 text-slate-300 q-mb-md")
            
            ui.separator().classes("q-my-md bg-slate-800")
            
            ui.label("Advanced Technology Pillars").classes("text-h5 text-weight-bold text-gradient-blue-purple q-mb-sm")
            
            with ui.row().classes("w-full q-col-gutter-md q-pt-sm text-left"):
                # Pillar 1
                with ui.column().classes("col-12 col-sm-6 q-mb-md"):
                    with ui.row().classes("items-center q-gutter-sm q-mb-xs"):
                        ui.icon("radar", size="2rem").classes("text-blue-400")
                        ui.label("3D Face Landmark Meshing").classes("text-subtitle1 text-weight-bold text-white")
                    ui.label("Extracts 1,404 precise facial landmarks to verify sightings and cross-reference public uploads against case databases instantly.").classes("text-body2 text-slate-400")
                
                # Pillar 2
                with ui.column().classes("col-12 col-sm-6 q-mb-md"):
                    with ui.row().classes("items-center q-gutter-sm q-mb-xs"):
                        ui.icon("psychology", size="2rem").classes("text-purple-400")
                        ui.label("RAG timeline analysis").classes("text-subtitle1 text-weight-bold text-white")
                    ui.label("Vector indexes investigative reports and witness statements. Generates interactive chat insights via local Ollama models.").classes("text-body2 text-slate-400")
                
                # Pillar 3
                with ui.column().classes("col-12 col-sm-6"):
                    with ui.row().classes("items-center q-gutter-sm q-mb-xs"):
                        ui.icon("update", size="2rem").classes("text-teal-400")
                        ui.label("Diffusion Age Progression").classes("text-subtitle1 text-weight-bold text-white")
                    ui.label("Uses conditioning filters to generate realistic age progressed appearance predictions for long-term missing persons.").classes("text-body2 text-slate-400")
                
                # Pillar 4
                with ui.column().classes("col-12 col-sm-6"):
                    with ui.row().classes("items-center q-gutter-sm q-mb-xs"):
                        ui.icon("map", size="2rem").classes("text-red-400")
                        ui.label("GIS Location Heatmaps").classes("text-subtitle1 text-weight-bold text-white")
                    ui.label("Visualizes cluster analysis of sighting reports, helping officers track physical search radii and regional trends.").classes("text-body2 text-slate-400")


    # Dynamic wide glass-footer
    with ui.element("footer").classes("glass-footer q-py-xl q-px-lg q-mt-xl"):
        with ui.row().classes("w-full max-w-7xl mx-auto q-col-gutter-lg justify-between items-start text-left"):
            # Column 1: Logo & Tagline
            with ui.column().classes("col-12 col-md-3 q-gutter-xs"):
                with ui.row().classes("items-center q-gutter-sm"):
                    ui.icon("radar", size="2rem").classes("text-blue-500 animate-pulse")
                    ui.label("TraceAI").classes("text-h5 text-weight-bolder text-white tracking-wider")
                ui.label("Finding Hope Through Intelligence").classes("text-caption text-blue-300 italic q-mb-sm")
                ui.label("Next-generation intelligence platform to locate missing citizens using advanced AI facemeshing, RAG timelines, and geolocation tracking.").classes("text-caption text-slate-400")

            # Column 2: Get Started
            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("Get started").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("Home", "/").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Public Sighting", "/public").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Portal Login", "/login").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")

            # Column 3: About Us
            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("About us").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("Company Info", "/company").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Contact us", "/contact").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.label("Reviews").classes("text-caption text-slate-400 cursor-pointer hover:text-blue-400 transition-colors")

            # Column 4: Support
            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("Support").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("FAQ", "/faq").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Help desk", "/helpdesk").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Forums", "/forums").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")

            # Column 5: Social & Action Button
            with ui.column().classes("col-12 col-md-3 items-start md:items-end q-gutter-sm"):
                with ui.row().classes("q-gutter-md q-mb-sm"):
                    ui.icon("chat", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                    ui.icon("public", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                    ui.icon("alternate_email", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                ui.button("Contact us", on_click=lambda: ui.navigate.to("/contact")).classes("rounded-full q-px-md").props("color=blue size=sm")

        ui.separator().classes("q-my-lg bg-slate-800")
        with ui.row().classes("w-full justify-center text-center"):
            ui.label("© 2026 TraceAI. Finding Hope Through Intelligence. All Rights Reserved.").classes("text-caption text-slate-500")
