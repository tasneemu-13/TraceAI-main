from nicegui import ui, app
from app.frontend import layout

def content():
    """
    Renders the premium Contact Us page.
    """
    layout.theme_setup()
    
    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md q-mb-xl"):
        # Top distraction-free navigation back to home
        with ui.row().classes("w-full max-w-5xl justify-start items-center q-mb-md"):
            ui.button("Back to Home", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("glass-btn text-blue-400").props("flat dense")
            
        # Header title
        ui.label("Contact TraceAI Support").classes("text-h3 text-weight-bolder text-white q-mb-xs text-center")
        ui.label("Get in touch with our emergency response and platform technical support teams.").classes("text-subtitle1 text-slate-400 q-mb-xl text-center")
        
        # Grid layout for Form + Contact Details
        with ui.row().classes("w-full max-w-5xl q-col-gutter-lg justify-center items-stretch"):
            
            # LEFT: Contact Form Card
            with ui.card().classes("col-12 col-md-7 glass-card q-pa-lg flex flex-col justify-between"):
                ui.label("Send us a Message").classes("text-h5 text-weight-bold text-white q-mb-md")
                
                with ui.column().classes("w-full q-gutter-sm"):
                    name_input = ui.input("Full Name").props("outlined dense").classes("w-full")
                    email_input = ui.input("Email Address").props("outlined dense").classes("w-full")
                    subject_input = ui.input("Subject").props("outlined dense").classes("w-full")
                    message_input = ui.textarea("Message Details").props("outlined dense placeholder='Describe your inquiry, case issue, or feedback...'").classes("w-full q-mb-md")
                    
                    def submit_contact():
                        n = name_input.value.strip()
                        e = email_input.value.strip()
                        s = subject_input.value.strip()
                        m = message_input.value.strip()
                        
                        if not all([n, e, s, m]):
                            ui.notify("Please fill in all the fields.", type="warning")
                            return
                            
                        # Success Notification
                        ui.notify("Thank you! Your message has been sent to TraceAI Support.", type="positive")
                        
                        # Reset fields
                        name_input.value = ""
                        email_input.value = ""
                        subject_input.value = ""
                        message_input.value = ""
                        
                    ui.button("Send Message", on_click=submit_contact).classes("w-full q-py-sm").props("color=blue")

            # RIGHT: Contact Info Card
            with ui.card().classes("col-12 col-md-5 glass-card q-pa-lg text-white flex flex-col justify-between"):
                ui.label("Direct Support Channels").classes("text-h5 text-weight-bold text-white q-mb-md")
                
                with ui.column().classes("w-full q-gutter-md"):
                    # channel 1: email
                    with ui.row().classes("items-center q-gutter-md"):
                        ui.icon("alternate_email", size="2.5rem").classes("text-blue-400")
                        with ui.column():
                            ui.label("Email Inquiries").classes("text-subtitle2 text-slate-400 q-mb-none")
                            ui.label("support@traceai.gov.in").classes("text-subtitle1 text-weight-bold text-white")
                            
                    # channel 2: phone
                    with ui.row().classes("items-center q-gutter-md"):
                        ui.icon("phone", size="2.5rem").classes("text-teal-400")
                        with ui.column():
                            ui.label("Emergency Call Center").classes("text-subtitle2 text-slate-400 q-mb-none")
                            ui.label("+1 (800) TRACE-AI").classes("text-subtitle1 text-weight-bold text-white")
                            
                    # channel 3: address
                    with ui.row().classes("items-center q-gutter-md"):
                        ui.icon("location_on", size="2.5rem").classes("text-purple-400")
                        with ui.column():
                            ui.label("Headquarters").classes("text-subtitle2 text-slate-400 q-mb-none")
                            ui.label("CGO Complex, Lodhi Road, New Delhi, India").classes("text-subtitle1 text-weight-bold text-white")
                            
                # Nice reassurance tagline
                ui.separator().classes("q-my-md bg-slate-800")
                ui.label("Emergency missing cases should also be reported via local citizen portals or dialing 100/112 immediately.").classes("text-caption text-red-300 text-weight-bold italic")



    # Dynamic wide glass-footer
    # Footer Section matching the reference layout & current theme
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
                # Social Icons Row
                with ui.row().classes("q-gutter-md q-mb-sm"):
                    ui.icon("chat", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                    ui.icon("public", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                    ui.icon("alternate_email", size="1.5rem").classes("text-slate-400 hover:text-blue-400 cursor-pointer transition-colors")
                
                # Pill button matching the theme
                ui.button("Contact us", on_click=lambda: ui.navigate.to("/contact")).classes("rounded-full q-px-md").props("color=blue size=sm")

        # Divider line
        ui.separator().classes("q-my-lg bg-slate-800")
        
        # Bottom Copyright bar
        with ui.row().classes("w-full justify-center text-center"):
            ui.label("© 2026 TraceAI. Finding Hope Through Intelligence. All Rights Reserved.").classes("text-caption text-slate-500")
