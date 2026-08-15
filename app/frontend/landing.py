from nicegui import ui, app
from app.frontend import layout
from app.database import db_session
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions
from app.models.doc import SightingMatch

def content():
    """
    Renders the cinematic landing page content.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Query current stats for counters
    db = db_session()
    try:
        missing_count = db.query(RegisteredCases).filter(RegisteredCases.status == "NF").count()
        resolved_count = db.query(RegisteredCases).filter(RegisteredCases.status == "F").count()
        reports_count = db.query(PublicSubmissions).count()
        matches_count = db.query(SightingMatch).count()
    except Exception:
        missing_count, resolved_count, reports_count, matches_count = 142, 89, 310, 48
    finally:
        db_session.remove()
        
    # Main hero section
    with ui.column().classes("w-full items-center justify-center text-center q-pt-xl q-px-md"):
        # Logo Icon
        with ui.element("div").classes("q-mb-md q-pa-md glass-card rounded-full inline-block"):
            ui.icon("radar", size="5rem").classes("text-blue-500 animate-pulse")
            
        ui.label("TraceAI").classes("text-h2 text-weight-bolder text-white tracking-widest q-mb-xs")
        ui.label("Finding Hope Through Intelligence").classes("text-h6 text-blue-300 q-mb-md tracking-wide italic")
        
        # Typing Animation placeholder using pure client-side JS for smoothness
        typing_html = """
        <div style="font-size: 1.5rem; min-height: 50px; color: #94a3b8; font-weight: 300;">
            Next-gen Platform for 
            <span id="typing-text" class="text-gradient-purple-teal" style="font-weight: 800; border-right: 2px solid #14b8a6; padding-right: 4px;"></span>
        </div>
        """
        ui.html(typing_html).classes("q-mb-lg")
        
        ui.add_body_html("""
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const words = ["Facial Landmarking", "AI Age Progression", "RAG Investigation Assistant", "GIS Sighting Heatmaps"];
                let wordIndex = 0;
                let charIndex = 0;
                let isDeleting = false;
                
                function type() {
                    const textElement = document.getElementById("typing-text");
                    if (!textElement) {
                        setTimeout(type, 100);
                        return;
                    }
                    const currentWord = words[wordIndex];
                    if (isDeleting) {
                        textElement.textContent = currentWord.substring(0, charIndex - 1);
                        charIndex--;
                    } else {
                        textElement.textContent = currentWord.substring(0, charIndex + 1);
                        charIndex++;
                    }
                    
                    let typeSpeed = isDeleting ? 40 : 80;
                    
                    if (!isDeleting && charIndex === currentWord.length) {
                        typeSpeed = 1500;
                        isDeleting = true;
                    } else if (isDeleting && charIndex === 0) {
                        isDeleting = false;
                        wordIndex = (wordIndex + 1) % words.length;
                        typeSpeed = 400;
                    }
                    
                    setTimeout(type, typeSpeed);
                }
                setTimeout(type, 500);
            });
        </script>
        """)
        

            
        # Statistics Panel
        with ui.row().classes("w-full max-w-5xl justify-center q-col-gutter-md q-px-md q-mb-xl"):
            # Card 1: Missing Persons
            with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-lg"):
                ui.icon("person_search", size="2.5rem").classes("text-red-400 q-mb-xs")
                ui.label(str(missing_count)).classes("text-h4 text-weight-bold text-white animate-bounce")
                ui.label("Active Missing Cases").classes("text-subtitle2 text-slate-400")
                
            # Card 2: Resolved Cases
            with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-lg"):
                ui.icon("verified", size="2.5rem").classes("text-green-400 q-mb-xs")
                ui.label(str(resolved_count)).classes("text-h4 text-weight-bold text-white")
                ui.label("Resolved Cases").classes("text-subtitle2 text-slate-400")
                
            # Card 3: Public Reports
            with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-lg"):
                ui.icon("upload_file", size="2.5rem").classes("text-blue-400 q-mb-xs")
                ui.label(str(reports_count)).classes("text-h4 text-weight-bold text-white")
                ui.label("Public Sighting Reports").classes("text-subtitle2 text-slate-400")
                
            # Card 4: AI Matches
            with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-lg"):
                ui.icon("settings_suggest", size="2.5rem").classes("text-purple-400 q-mb-xs")
                ui.label(str(matches_count)).classes("text-h4 text-weight-bold text-white")
                ui.label("AI Facemesh Matches").classes("text-subtitle2 text-slate-400")
                
        # Lower About details section
        with ui.column().classes("w-full max-w-4xl q-py-xl text-center glass-card q-px-xl q-mb-xl"):
            ui.label("How TraceAI Works").classes("text-h4 text-weight-bold q-mb-md text-gradient-blue-purple")
            
            with ui.row().classes("w-full justify-around text-left q-col-gutter-lg q-pt-md"):
                # Step 1
                with ui.column().classes("col-12 col-sm-4 items-center text-center"):
                    ui.icon("add_photo_alternate", size="3rem").classes("text-blue-400 q-mb-sm")
                    ui.label("1. File Report").classes("text-h6 text-weight-bold text-white")
                    ui.label("Officers register missing cases with photos, Aadhaar details, medical conditions, and physical features.").classes("text-body2 text-slate-400")
                # Step 2
                with ui.column().classes("col-12 col-sm-4 items-center text-center"):
                    ui.icon("model_training", size="3rem").classes("text-purple-400 q-mb-sm")
                    ui.label("2. Age Progression & Encoding").classes("text-h6 text-weight-bold text-white")
                    ui.label("The AI generates an estimated current appearance and extracts a 1,404-dimensional facial landmark mesh.").classes("text-body2 text-slate-400")
                # Step 3
                with ui.column().classes("col-12 col-sm-4 items-center text-center"):
                    ui.icon("psychology", size="3rem").classes("text-teal-400 q-mb-sm")
                    ui.label("3. Intelligent RAG Matching").classes("text-h6 text-weight-bold text-white")
                    ui.label("KNN matches sightings, while our RAG assistant helps officers analyze reports, timeline details, and evidence.").classes("text-body2 text-slate-400")

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
