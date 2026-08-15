from nicegui import ui, app
from app.frontend import layout

def content():
    """
    Renders the premium FAQs page.
    """
    layout.theme_setup()
    
    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md q-mb-xl"):
        # Top distraction-free navigation back to home
        with ui.row().classes("w-full max-w-4xl justify-start items-center q-mb-md"):
            ui.button("Back to Home", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("glass-btn text-blue-400").props("flat dense")
            
        # Header title
        ui.label("Frequently Asked Questions").classes("text-h3 text-weight-bolder text-white q-mb-xs text-center")
        ui.label("Find quick answers about TraceAI's capabilities, matching algorithms, and security details.").classes("text-subtitle1 text-slate-400 q-mb-xl text-center")
        
        # FAQ Accordion Card
        with ui.card().classes("w-full max-w-4xl glass-card q-pa-lg text-white q-mb-lg"):
            
            # FAQ 1
            with ui.expansion("How accurate is the AI Age Progression?", icon="insights").classes("w-full border-b border-slate-800 text-subtitle1 font-bold q-py-sm"):
                ui.label(
                    "The model utilizes advanced img2img latent diffusion networks conditioned on age scaling parameters. "
                    "It predicts structures, cranial shapes, and skin textures. While mathematically rigorous, "
                    "the photos are intended to serve as investigative estimates and should be verified in the field."
                ).classes("text-body2 text-slate-400 q-pl-md q-pb-md")
                
            # FAQ 2
            with ui.expansion("How do public sighting submissions work?", icon="public").classes("w-full border-b border-slate-800 text-subtitle1 font-bold q-py-sm"):
                ui.label(
                    "Citizens can report sightings anonymously or with contact details via the 'Public Sighting' portal. "
                    "If a face photo is uploaded, our system extracts facial landmarks in real-time and runs a "
                    "KNN classification match against active cases. If a close match is identified, station officers "
                    "are immediately alerted to verify the sighting."
                ).classes("text-body2 text-slate-400 q-pl-md q-pb-md")

            # FAQ 3
            with ui.expansion("Who has access to the database and cases?", icon="security").classes("w-full border-b border-slate-800 text-subtitle1 font-bold q-py-sm"):
                ui.label(
                    "Access is partitioned by role-based security: "
                    "Public users can only view case alerts and submit sightings. "
                    "Station Officers can register cases, add investigation log reports, and review AI matches. "
                    "Administrators manage credentials, system diagnostic checks, and SMTP configurations."
                ).classes("text-body2 text-slate-400 q-pl-md q-pb-md")

            # FAQ 4
            with ui.expansion("How does the RAG investigation assistant help officers?", icon="chat").classes("w-full border-b border-slate-800 text-subtitle1 font-bold q-py-sm"):
                ui.label(
                    "The Retrieval-Augmented Generation (RAG) assistant is a local AI copilot. "
                    "It vectorizes case details, witness reports, and logs using local vector models. "
                    "When an officer queries the case history, it pulls the most relevant evidence documents "
                    "and asks a local Ollama model to summarize geographic patterns, timeline clues, and conflicting statements."
                ).classes("text-body2 text-slate-400 q-pl-md q-pb-md")

            # FAQ 5
            with ui.expansion("Is my personal data saved when registering anonymous sightings?", icon="lock").classes("w-full text-subtitle1 font-bold q-py-sm"):
                ui.label(
                    "No. Anonymous submissions only store the sighting location, description, and optional photo. "
                    "No IP logs, session data, or personal details are persisted, preserving complete citizen privacy."
                ).classes("text-body2 text-slate-400 q-pl-md q-pb-md")


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
