from nicegui import ui, app
from app.frontend import layout

def content():
    """
    Renders the premium Help Desk / Support Ticket page.
    """
    layout.theme_setup()

    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md q-mb-xl"):
        # Top navigation back to home
        with ui.row().classes("w-full max-w-5xl justify-start items-center q-mb-md"):
            ui.button("Back to Home", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("glass-btn text-blue-400").props("flat dense")

        # Header
        ui.label("Help Desk").classes("text-h3 text-weight-bolder text-white q-mb-xs text-center")
        ui.label("Submit a support ticket and our team will respond within 24 hours.").classes("text-subtitle1 text-slate-400 q-mb-xl text-center")

        # Status Banner
        with ui.card().classes("w-full max-w-5xl glass-card q-pa-md q-mb-lg"):
            with ui.row().classes("items-center q-gutter-md"):
                ui.icon("check_circle", size="2rem").classes("text-green-400")
                with ui.column().classes("q-gutter-none"):
                    ui.label("All Systems Operational").classes("text-subtitle1 text-weight-bold text-white")
                    ui.label("Platform uptime: 99.97% | Avg. response time: 4 hrs").classes("text-caption text-slate-400")

        # Main Grid
        with ui.row().classes("w-full max-w-5xl q-col-gutter-lg justify-center items-stretch"):

            # LEFT: Ticket Submission Form
            with ui.card().classes("col-12 col-md-7 glass-card q-pa-lg"):
                ui.label("Submit a Ticket").classes("text-h5 text-weight-bold text-white q-mb-md")

                with ui.column().classes("w-full q-gutter-sm"):
                    name_input    = ui.input("Full Name").props("outlined dense").classes("w-full")
                    email_input   = ui.input("Email Address").props("outlined dense").classes("w-full")

                    category = ui.select(
                        label="Issue Category",
                        options=[
                            "Account / Login Issues",
                            "Case Registration Problem",
                            "AI Matching Error",
                            "Map / Location Issue",
                            "Technical Bug / Crash",
                            "Feature Request",
                            "Other"
                        ]
                    ).props("outlined dense").classes("w-full")

                    priority = ui.select(
                        label="Priority",
                        options=["Low", "Medium", "High", "Critical"]
                    ).props("outlined dense").classes("w-full")

                    desc_input = ui.textarea("Describe your issue in detail").props(
                        "outlined dense placeholder='Please provide as much detail as possible — steps to reproduce, screenshots descriptions, error messages...'"
                    ).classes("w-full q-mb-sm")

                    def submit_ticket():
                        n = name_input.value.strip()
                        e = email_input.value.strip()
                        c = category.value
                        p = priority.value
                        d = desc_input.value.strip()

                        if not all([n, e, c, p, d]):
                            ui.notify("Please fill in all fields before submitting.", type="warning")
                            return

                        import random, string
                        ticket_id = "TKT-" + "".join(random.choices(string.digits, k=6))
                        ui.notify(f"✅ Ticket {ticket_id} submitted! We'll contact you at {e} within 24 hours.", type="positive", timeout=6000)

                        # Reset
                        name_input.value = ""
                        email_input.value = ""
                        category.value = None
                        priority.value = None
                        desc_input.value = ""

                    ui.button("Submit Ticket", icon="send", on_click=submit_ticket).classes("w-full q-py-sm").props("color=blue")

            # RIGHT: Support Info
            with ui.card().classes("col-12 col-md-5 glass-card q-pa-lg text-white"):
                ui.label("Support Information").classes("text-h5 text-weight-bold text-white q-mb-md")

                with ui.column().classes("w-full q-gutter-lg"):
                    # SLA info
                    with ui.card().classes("glass-card q-pa-md"):
                        with ui.row().classes("items-center q-gutter-sm q-mb-sm"):
                            ui.icon("timer", size="1.8rem").classes("text-blue-400")
                            ui.label("Response SLA").classes("text-subtitle1 text-weight-bold")
                        with ui.column().classes("q-gutter-xs q-pl-sm"):
                            ui.label("🔴 Critical — Within 2 hours").classes("text-caption text-slate-300")
                            ui.label("🟠 High — Within 8 hours").classes("text-caption text-slate-300")
                            ui.label("🟡 Medium — Within 24 hours").classes("text-caption text-slate-300")
                            ui.label("🟢 Low — Within 48 hours").classes("text-caption text-slate-300")

                    # Quick links
                    with ui.card().classes("glass-card q-pa-md"):
                        with ui.row().classes("items-center q-gutter-sm q-mb-sm"):
                            ui.icon("quick_reference_all", size="1.8rem").classes("text-purple-400")
                            ui.label("Quick Resources").classes("text-subtitle1 text-weight-bold")
                        with ui.column().classes("q-gutter-xs"):
                            ui.button("Browse FAQ", icon="help_outline",
                                      on_click=lambda: ui.navigate.to("/faq")).props("flat dense align=left").classes("text-blue-400 w-full")
                            ui.button("Community Forums", icon="forum",
                                      on_click=lambda: ui.navigate.to("/forums")).props("flat dense align=left").classes("text-teal-400 w-full")
                            ui.button("Contact Us Directly", icon="alternate_email",
                                      on_click=lambda: ui.navigate.to("/contact")).props("flat dense align=left").classes("text-green-400 w-full")

                    # Emergency
                    with ui.card().classes("q-pa-md").style("background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);"):
                        with ui.row().classes("items-center q-gutter-sm q-mb-xs"):
                            ui.icon("emergency", size="1.8rem").classes("text-red-400")
                            ui.label("Emergency Cases").classes("text-subtitle1 text-weight-bold text-red-300")
                        ui.label("For urgent missing person emergencies, call 100 or 112 immediately. Do not rely solely on this portal.").classes("text-caption text-red-200")

    # Footer
    with ui.element("footer").classes("glass-footer q-py-xl q-px-lg q-mt-xl"):
        with ui.row().classes("w-full max-w-7xl mx-auto q-col-gutter-lg justify-between items-start text-left"):
            with ui.column().classes("col-12 col-md-3 q-gutter-xs"):
                with ui.row().classes("items-center q-gutter-sm"):
                    ui.icon("radar", size="2rem").classes("text-blue-500 animate-pulse")
                    ui.label("TraceAI").classes("text-h5 text-weight-bolder text-white tracking-wider")
                ui.label("Finding Hope Through Intelligence").classes("text-caption text-blue-300 italic q-mb-sm")
                ui.label("Next-generation intelligence platform to locate missing citizens using advanced AI facemeshing, RAG timelines, and geolocation tracking.").classes("text-caption text-slate-400")

            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("Get started").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("Home", "/").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Public Sighting", "/public").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Portal Login", "/login").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")

            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("About us").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("Company Info", "/company").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Contact us", "/contact").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.label("Reviews").classes("text-caption text-slate-400")

            with ui.column().classes("col-6 col-md-2 q-gutter-xs"):
                ui.label("Support").classes("text-subtitle2 text-weight-bold text-white q-mb-sm")
                ui.link("FAQ", "/faq").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Help desk", "/helpdesk").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")
                ui.link("Forums", "/forums").classes("text-caption text-slate-400 hover:text-blue-400 transition-colors no-underline")

            with ui.column().classes("col-12 col-md-3 items-start q-gutter-sm"):
                with ui.row().classes("q-gutter-md q-mb-sm"):
                    ui.icon("chat", size="1.5rem").classes("text-slate-400 cursor-pointer")
                    ui.icon("public", size="1.5rem").classes("text-slate-400 cursor-pointer")
                    ui.icon("alternate_email", size="1.5rem").classes("text-slate-400 cursor-pointer")
                ui.button("Contact us", on_click=lambda: ui.navigate.to("/contact")).classes("rounded-full q-px-md").props("color=blue size=sm")

        ui.separator().classes("q-my-lg bg-slate-800")
        with ui.row().classes("w-full justify-center text-center"):
            ui.label("© 2026 TraceAI. Finding Hope Through Intelligence. All Rights Reserved.").classes("text-caption text-slate-500")
