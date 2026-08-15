from nicegui import ui, app
from app.frontend import layout

def content():
    """
    Renders the Community Forums page.
    """
    layout.theme_setup()

    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md q-mb-xl"):
        # Top navigation
        with ui.row().classes("w-full max-w-5xl justify-start items-center q-mb-md"):
            ui.button("Back to Home", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).classes("glass-btn text-blue-400").props("flat dense")

        # Header
        ui.label("Community Forums").classes("text-h3 text-weight-bolder text-white q-mb-xs text-center")
        ui.label("Discuss cases, share tips, and collaborate with officers and investigators across the country.").classes("text-subtitle1 text-slate-400 q-mb-xl text-center")

        # Stats Row
        with ui.row().classes("w-full max-w-5xl q-col-gutter-md q-mb-lg justify-center"):
            for icon, val, label, color in [
                ("forum",        "1,248", "Total Threads",    "text-blue-400"),
                ("people",       "342",   "Active Members",   "text-teal-400"),
                ("mark_chat_read","8,901","Total Replies",    "text-purple-400"),
                ("trending_up",  "24",    "New Today",        "text-green-400"),
            ]:
                with ui.card().classes("col-6 col-sm-3 glass-card q-pa-md items-center text-center"):
                    ui.icon(icon, size="2rem").classes(f"{color} q-mb-xs")
                    ui.label(val).classes("text-h5 text-weight-bold text-white")
                    ui.label(label).classes("text-caption text-slate-400")

        with ui.row().classes("w-full max-w-5xl q-col-gutter-lg"):

            # LEFT: Forum Categories
            with ui.column().classes("col-12 col-md-8 q-gutter-md"):
                ui.label("Discussion Categories").classes("text-h6 text-weight-bold text-white q-mb-sm")

                categories = [
                    ("🔍", "Case Discussions",         "Share insights and updates on active missing person cases.",           "142 threads", "text-blue-400"),
                    ("🤖", "AI & Technology",           "Discuss AI matching accuracy, MediaPipe tips, and model improvements.", "87 threads",  "text-purple-400"),
                    ("🗺️", "Field Investigations",      "Coordinate search efforts, share location leads, and field reports.",  "203 threads", "text-teal-400"),
                    ("📋", "Platform Guides & How-Tos", "Tutorials, walkthroughs and best practices for using TraceAI.",        "56 threads",  "text-green-400"),
                    ("🚨", "Alerts & Urgent Sightings", "Time-sensitive sighting alerts that need immediate attention.",         "34 threads",  "text-red-400"),
                    ("💡", "Feature Suggestions",       "Propose and vote on new features for the TraceAI platform.",           "91 threads",  "text-yellow-400"),
                ]

                for emoji, title, desc, count, color in categories:
                    with ui.card().classes("w-full glass-card q-pa-md cursor-pointer hover:opacity-90 transition-opacity"):
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.row().classes("items-center q-gutter-md"):
                                ui.label(emoji).classes("text-h4")
                                with ui.column().classes("q-gutter-none"):
                                    ui.label(title).classes(f"text-subtitle1 text-weight-bold {color}")
                                    ui.label(desc).classes("text-caption text-slate-400")
                            ui.badge(count).classes("text-caption").props("color=dark")

                # Recent Threads
                ui.label("Recent Threads").classes("text-h6 text-weight-bold text-white q-mt-md q-mb-sm")

                threads = [
                    ("Best practices for uploading sighting photos",           "Officer_Ravi",    "2 hrs ago",  "12 replies"),
                    ("KNN confidence threshold — what score is reliable?",     "AI_Analyst_98",   "5 hrs ago",  "8 replies"),
                    ("Missing child — Mumbai Central — urgent sighting lead",   "Inspector_Shah",  "6 hrs ago",  "31 replies"),
                    ("How to use the RAG assistant for timeline analysis",      "Tasneem",         "1 day ago",  "5 replies"),
                    ("Suggestion: add SMS alert when a case status changes",    "Officer_Priya",   "2 days ago", "14 replies"),
                ]

                for title, author, time_ago, replies in threads:
                    with ui.card().classes("w-full glass-card q-pa-sm"):
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.row().classes("items-center q-gutter-md"):
                                ui.icon("chat_bubble_outline", size="1.5rem").classes("text-slate-500")
                                with ui.column().classes("q-gutter-none"):
                                    ui.label(title).classes("text-body2 text-weight-medium text-white")
                                    ui.label(f"by {author} · {time_ago}").classes("text-caption text-slate-500")
                            ui.label(replies).classes("text-caption text-slate-400")

            # RIGHT: Sidebar
            with ui.column().classes("col-12 col-md-4 q-gutter-md"):

                # Post a Thread card
                with ui.card().classes("glass-card q-pa-lg w-full"):
                    ui.label("Start a Discussion").classes("text-subtitle1 text-weight-bold text-white q-mb-sm")
                    thread_title = ui.input("Thread Title").props("outlined dense").classes("w-full q-mb-sm")
                    thread_body  = ui.textarea("Your message").props("outlined dense").classes("w-full q-mb-sm")

                    def post_thread():
                        if not thread_title.value.strip() or not thread_body.value.strip():
                            ui.notify("Please fill in both fields.", type="warning")
                            return
                        ui.notify("✅ Thread posted successfully!", type="positive")
                        thread_title.value = ""
                        thread_body.value  = ""

                    ui.button("Post Thread", icon="send", on_click=post_thread).props("color=blue").classes("w-full")

                # Top Contributors
                with ui.card().classes("glass-card q-pa-md w-full"):
                    ui.label("Top Contributors").classes("text-subtitle1 text-weight-bold text-white q-mb-sm")
                    contributors = [
                        ("Inspector_Shah",  "142 posts", "text-yellow-400",  "emoji_events"),
                        ("AI_Analyst_98",   "98 posts",  "text-slate-300",   "military_tech"),
                        ("Officer_Priya",   "76 posts",  "text-amber-600",   "workspace_premium"),
                        ("Tasneem",         "54 posts",  "text-blue-400",    "star"),
                        ("Officer_Ravi",    "41 posts",  "text-teal-400",    "thumb_up"),
                    ]
                    for name, posts, color, icon in contributors:
                        with ui.row().classes("items-center justify-between w-full q-py-xs"):
                            with ui.row().classes("items-center q-gutter-sm"):
                                ui.icon(icon, size="1.2rem").classes(color)
                                ui.label(name).classes("text-caption text-white")
                            ui.label(posts).classes("text-caption text-slate-400")

                # Quick links
                with ui.card().classes("glass-card q-pa-md w-full"):
                    ui.label("Quick Links").classes("text-subtitle1 text-weight-bold text-white q-mb-sm")
                    ui.button("FAQ", icon="help_outline",
                              on_click=lambda: ui.navigate.to("/faq")).props("flat dense align=left").classes("text-blue-400 w-full")
                    ui.button("Help Desk", icon="support_agent",
                              on_click=lambda: ui.navigate.to("/helpdesk")).props("flat dense align=left").classes("text-purple-400 w-full")
                    ui.button("Contact Us", icon="alternate_email",
                              on_click=lambda: ui.navigate.to("/contact")).props("flat dense align=left").classes("text-teal-400 w-full")

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
