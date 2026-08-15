import os
import json
import base64
from datetime import datetime
from uuid import uuid4
from nicegui import ui, app
from app.frontend import layout
from app.database import db_session
from app.repositories import case as case_repo
from app.repositories import submission as sub_repo
from app.models.case import RegisteredCases
from app.models.submission import PublicSubmissions
from app.models.doc import SightingMatch, InvestigationDoc
from app.services import matching as match_service
from app.services import age_progression as age_service
from app.services import notification as notify_service
from app.config import settings

def content():
    """
    Renders the Officer Dashboard.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Force authentication
    username = app.storage.user.get("user")
    role = app.storage.user.get("role")
    if not username:
        ui.navigate.to("/login")
        return
        
    db = db_session()
    try:
        # Load stats
        cases = case_repo.list_cases(db, submitted_by=username)
        all_cases = case_repo.list_cases(db)
        total_open = len([c for c in all_cases if c.status == "NF"])
        total_resolved = len([c for c in all_cases if c.status == "F"])
        
        # Public sightings and matches
        pending_matches = db.query(SightingMatch).filter(SightingMatch.status == "Pending").all()
        sighting_count = db.query(PublicSubmissions).count()
        
    except Exception as e:
        total_open, total_resolved, pending_matches, sighting_count = 0, 0, [], 0
    finally:
        db_session.remove()

    # Active view state
    active_tab = {"value": "Dashboard"}

    with ui.column().classes("w-full q-pa-md"):
        # Header banner
        with ui.row().classes("w-full justify-between items-center q-mb-md"):
            with ui.column():
                ui.label(f"Welcome, Officer {app.storage.user.get('name', username)}").classes("text-h4 text-weight-bold text-white")
                ui.label(f"TraceAI Hub — Active station logs").classes("text-caption text-slate-400")
            ui.button("Register New Case", icon="add_box", on_click=lambda: show_tab("Register")).classes("glass-btn text-blue-400 q-px-md").props("size=md")

        # Tabs bar
        with ui.row().classes("w-full justify-center q-mb-md"):
            with ui.card().classes("glass-card row w-full justify-around q-col-gutter-xs q-pa-sm"):
                btn_dash = ui.button("Dashboard Overview", icon="dashboard", on_click=lambda: show_tab("Dashboard")).classes("col glass-btn text-blue-400")
                btn_cases = ui.button("Active Investigation Files", icon="folder_open", on_click=lambda: show_tab("Cases")).classes("col glass-btn")
                btn_alerts = ui.button(f"AI Matches ({len(pending_matches)})", icon="notification_important", on_click=lambda: show_tab("Alerts")).classes("col glass-btn")
                btn_match = ui.button("Check for Match", icon="insights", on_click=lambda: show_tab("Match")).classes("col glass-btn")
                
        # Views containers
        container_dash = ui.column().classes("w-full q-col-gutter-md row")
        container_cases = ui.column().classes("w-full q-gutter-md").style("display: none;")
        container_alerts = ui.column().classes("w-full q-gutter-md").style("display: none;")
        container_register = ui.column().classes("w-full max-w-3xl items-center q-gutter-md mx-auto").style("display: none;")
        container_match = ui.column().classes("w-full max-w-4xl q-gutter-md mx-auto").style("display: none;")
        
        def show_tab(tab_name: str):
            active_tab["value"] = tab_name
            
            btn_dash.classes(remove="text-blue-400")
            btn_cases.classes(remove="text-blue-400")
            btn_alerts.classes(remove="text-blue-400")
            btn_match.classes(remove="text-blue-400")
            
            container_dash.style("display: none;")
            container_cases.style("display: none;")
            container_alerts.style("display: none;")
            container_register.style("display: none;")
            container_match.style("display: none;")
            
            if tab_name == "Dashboard":
                btn_dash.classes("text-blue-400")
                container_dash.style("display: flex;")
                render_map() # Re-trigger client map render when viewing dashboard
            elif tab_name == "Cases":
                btn_cases.classes("text-blue-400")
                container_cases.style("display: flex;")
            elif tab_name == "Alerts":
                btn_alerts.classes("text-blue-400")
                container_alerts.style("display: flex;")
            elif tab_name == "Match":
                btn_match.classes("text-blue-400")
                container_match.style("display: flex;")
                render_match_dashboard()
            else:
                container_register.style("display: flex;")

        # ── TAB 1: DASHBOARD OVERVIEW (MAPS & ANALYTICS) ────────────────────────
        with container_dash:
            # Metrics
            with ui.row().classes("col-12 q-col-gutter-md q-mb-md"):
                # Metrics 1: Open Cases
                with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-md"):
                    ui.label("Active Missing").classes("text-caption text-slate-400")
                    ui.label(str(total_open)).classes("text-h4 text-weight-bold text-white")
                # Metrics 2: Resolved Cases
                with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-md"):
                    ui.label("Located Citizens").classes("text-caption text-slate-400")
                    ui.label(str(total_resolved)).classes("text-h4 text-weight-bold text-white")
                # Metrics 3: Pending verification
                with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-md"):
                    ui.label("Unverified Sighting Matches").classes("text-caption text-slate-400")
                    ui.label(str(len(pending_matches))).classes("text-h4 text-weight-bold text-purple-400 animate-pulse")
                # Metrics 4: Sighting Reports
                with ui.card().classes("col-12 col-sm-3 glass-card items-center text-center q-pa-md"):
                    ui.label("Total Logged Sightings").classes("text-caption text-slate-400")
                    ui.label(str(sighting_count)).classes("text-h4 text-weight-bold text-white")
            
            # India Heatmap GIS Map Card
            with ui.card().classes("col-12 glass-card q-pa-md q-mb-md"):
                ui.label("🗺️ Regional Cases Map").classes("text-subtitle1 text-weight-bold text-white q-mb-xs")
                
                # Leaflet Mount Element
                ui.html('<div id="leaflet-map" style="width: 100%; height: 480px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);"></div>').classes('w-full')
                
                # Legend below the map matching user mockup
                ui.html("""
                <div class="row items-center q-gutter-md q-mt-sm text-caption text-slate-300">
                    <div class="row items-center q-gutter-xs">
                        <span style="display: inline-block; width: 10px; height: 10px; background-color: #ef4444; border-radius: 50%;"></span>
                        <span>Has unresolved cases</span>
                    </div>
                    <div class="row items-center q-gutter-xs">
                        <span style="display: inline-block; width: 10px; height: 10px; background-color: #22c55e; border-radius: 50%;"></span>
                        <span>All cases resolved</span>
                    </div>
                    <span>• Circle size maps to number of cases</span>
                </div>
                """)
                
                # Include Leaflet CSS/JS
                ui.add_head_html('<link rel="stylesheet" href="/static/leaflet.css" />')
                ui.add_head_html('<script src="/static/leaflet.js"></script>')
                ui.add_head_html('<style>#leaflet-map { width: 100% !important; min-width: 100% !important; display: block !important; }</style>')

        # Client-side map rendering logic
        def render_map():
            db_conn = db_session()
            markers = []
            try:
                cases_list = case_repo.list_cases(db_conn)
                
                # Group cases by city
                city_groups = {}
                for c in cases_list:
                    city = c.city or "Unknown"
                    if city not in city_groups:
                        city_groups[city] = {
                            "total": 0,
                            "resolved": 0,
                            "unresolved": 0,
                            "names": []
                        }
                    city_groups[city]["total"] += 1
                    if c.status == "F":
                        city_groups[city]["resolved"] += 1
                    else:
                        city_groups[city]["unresolved"] += 1
                    city_groups[city]["names"].append(f"{c.name} ({'Found' if c.status == 'F' else 'Not Found'})")
                
                # City coordinates fallback
                from app.routes.map import CITY_COORDS
                
                for city, stats in city_groups.items():
                    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Unknown"])
                    
                    # Color check: red if any unresolved, green if all resolved
                    color = "#ef4444" if stats["unresolved"] > 0 else "#22c55e"
                    
                    # Radius proportional to number of cases
                    radius = 8 + (stats["total"] * 3)
                    if radius > 40:
                        radius = 40
                        
                    # Popup Info HTML
                    names_list = "<br>".join(stats["names"][:5])
                    if len(stats["names"]) > 5:
                        names_list += "<br>... and more"
                        
                    info_html = (
                        f"<b>City: {city}</b><br>"
                        f"Total Cases: {stats['total']}<br>"
                        f"Unresolved: {stats['unresolved']}<br>"
                        f"Resolved: {stats['resolved']}<br><br>"
                        f"<b>Profiles:</b><br>{names_list}"
                    )
                    
                    markers.append({
                        "lat": lat,
                        "lon": lon,
                        "color": color,
                        "radius": radius,
                        "info": info_html
                    })
            except Exception:
                pass
            finally:
                db_session.remove()
                
            # Inject Javascript into NiceGUI client to render Leaflet Light Map
            js_code = f"""
                setTimeout(function initMap() {{
                    console.log("[TraceAI Map] initMap started.");
                    
                    // Dynamically inject Leaflet CSS if not loaded
                    if (!document.getElementById('leaflet-css-link')) {{
                        console.log("[TraceAI Map] CSS link element missing. Injecting leaflet.css...");
                        var link = document.createElement('link');
                        link.id = 'leaflet-css-link';
                        link.rel = 'stylesheet';
                        link.href = '/static/leaflet.css';
                        document.head.appendChild(link);
                    }} else {{
                        console.log("[TraceAI Map] CSS link element found.");
                    }}
                    
                    // Dynamically inject Leaflet JS if not loaded
                    if (typeof L === 'undefined') {{
                        console.log("[TraceAI Map] Leaflet (L) is undefined. Injecting leaflet.js...");
                        if (!document.getElementById('leaflet-js-script')) {{
                            var script = document.createElement('script');
                            script.id = 'leaflet-js-script';
                            script.src = '/static/leaflet.js';
                            document.head.appendChild(script);
                        }}
                        setTimeout(initMap, 250);
                        return;
                    }} else {{
                        console.log("[TraceAI Map] Leaflet (L) is defined.");
                    }}
                    
                    var mapElement = document.getElementById('leaflet-map');
                    if (!mapElement) {{
                        console.log("[TraceAI Map] #leaflet-map container element not found in DOM yet. Retrying in 250ms...");
                        setTimeout(initMap, 250);
                        return;
                    }} else {{
                        console.log("[TraceAI Map] #leaflet-map container found. Height:", mapElement.clientHeight, "Width:", mapElement.clientWidth);
                    }}
                    
                    try {{
                        // Clear existing map instance if already initialized on this node
                        if (window.leafletMapObj) {{
                            console.log("[TraceAI Map] Removing existing map instance.");
                            window.leafletMapObj.remove();
                        }}
                        
                        console.log("[TraceAI Map] Initializing map...");
                        var map = L.map('leaflet-map').setView([20.5937, 78.9629], 5);
                        window.leafletMapObj = map;
                        
                        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
                        }}).addTo(map);
                        
                        console.log("[TraceAI Map] Base map tiles added successfully.");
                        
                        var markersData = {json.dumps(markers)};
                        console.log("[TraceAI Map] Mapping " + markersData.length + " marker points.");
                        markersData.forEach(function(m) {{
                            var marker = L.circleMarker([m.lat, m.lon], {{
                                color: m.color,
                                fillColor: m.color,
                                fillOpacity: 0.6,
                                radius: m.radius
                            }}).addTo(map);
                            marker.bindPopup(m.info);
                        }});
                        
                        setTimeout(function() {{
                            console.log("[TraceAI Map] Invalidating map rendering boundaries.");
                            map.invalidateSize();
                        }}, 150);
                        
                    }} catch (err) {{
                        console.error("[TraceAI Map Exception] Error initializing Leaflet Map:", err);
                    }}
                }}, 200);
            """
            ui.run_javascript(js_code)

        # ── TAB 2: ACTIVE CASES LIST ───────────────────────────────────────────
        with container_cases:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Registered Missing Person Case Files").classes("text-h6 text-weight-bold text-white q-mb-md")
                
                cases_list_row = ui.column().classes("w-full q-gutter-sm")
                
                def render_cases_list():
                    cases_list_row.clear()
                    db_conn = db_session()
                    try:
                        cases_all = case_repo.list_cases(db_conn)
                        if not cases_all:
                            with cases_list_row:
                                ui.label("No missing person case files logged in the system.").classes("text-subtitle2 text-slate-500 q-pa-md w-full text-center")
                            return
                            
                        with cases_list_row:
                            for c in cases_all:
                                with ui.card().classes("w-full glass-card q-pa-md row items-center justify-between").style("display: flex; flex-direction: row;"):
                                    with ui.row().classes("items-center q-gutter-md"):
                                        if c.original_image_path and os.path.exists(c.original_image_path):
                                            with open(c.original_image_path, "rb") as image_file:
                                                b64 = base64.b64encode(image_file.read()).decode("utf-8")
                                            ui.image(f"data:image/jpeg;base64,{b64}").classes("w-14 h-14 rounded-full object-cover")
                                        else:
                                            ui.icon("account_circle", size="3.5rem").classes("text-slate-600")
                                            
                                        with ui.column():
                                            ui.label(c.name).classes("text-subtitle1 text-weight-bold text-white")
                                            ui.label(f"Age: {c.age} | City: {c.city} | Reg: {c.submitted_on.strftime('%Y-%m-%d')}").classes("text-caption text-slate-400")
                                            
                                    with ui.row().classes("items-center q-gutter-sm"):
                                        badge_color = "red" if c.status == "NF" else "green"
                                        badge_text = "Not Found" if c.status == "NF" else "Found"
                                        ui.badge(badge_text, color=badge_color)
                                        ui.button("Open File", on_click=lambda case_id=c.id: ui.navigate.to(f"/cases/{case_id}")).classes("glass-btn text-blue-400")
                    except Exception as exc:
                        ui.notify(f"Failed to fetch cases list: {exc}", type="negative")
                    finally:
                        db_session.remove()

                render_cases_list()

        # ── TAB 3: PENDING MATCH REVIEW ALERTS ──────────────────────────────────
        with container_alerts:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("AI Face-Matching Pending Reviews").classes("text-h6 text-weight-bold text-white q-mb-xs")
                ui.label("Verify side-by-side landmark signatures and approve matches to resolve cases.").classes("text-caption text-slate-400 q-mb-md")
                
                alerts_list_row = ui.column().classes("w-full q-gutter-md")
                
                def render_alerts_list():
                    alerts_list_row.clear()
                    db_conn = db_session()
                    try:
                        matches = db_conn.query(SightingMatch).filter(SightingMatch.status == "Pending").all()
                        if not matches:
                            with alerts_list_row:
                                ui.label("No pending AI face-matching verification tasks.").classes("text-subtitle2 text-slate-500 q-pa-md w-full text-center")
                            return
                            
                        with alerts_list_row:
                            for m in matches:
                                case = case_repo.get_case_by_id(db_conn, m.case_id)
                                sub = sub_repo.get_submission_by_id(db_conn, m.submission_id)
                                
                                if not case or not sub:
                                    continue
                                    
                                with ui.card().classes("w-full glass-card q-pa-lg"):
                                    with ui.row().classes("w-full justify-between items-center border-b border-slate-700 q-pb-sm q-mb-md"):
                                        ui.label(f"Alert Match Ref: {m.id}").classes("text-caption text-blue-300 font-bold")
                                        ui.badge(f"Confidence: {m.confidence:.1f}%", color="purple")
                                        
                                    with ui.row().classes("w-full justify-around items-center q-mb-md"):
                                        # Registered Case Card
                                        with ui.column().classes("items-center col text-center"):
                                            ui.label("Registered Case Profile").classes("text-caption text-slate-400")
                                            if case.original_image_path and os.path.exists(case.original_image_path):
                                                with open(case.original_image_path, "rb") as image_file:
                                                    b64 = base64.b64encode(image_file.read()).decode("utf-8")
                                                ui.image(f"data:image/jpeg;base64,{b64}").classes("w-24 h-24 rounded object-cover q-mb-xs")
                                            ui.label(case.name).classes("text-subtitle2 text-white")
                                            ui.label(f"Age: {case.age}").classes("text-caption text-slate-500")
                                            
                                        # Age Progressed estimate
                                        with ui.column().classes("items-center col text-center"):
                                            ui.label("AI Age Progressed").classes("text-caption text-slate-400")
                                            if case.age_progressed_image_path and os.path.exists(case.age_progressed_image_path):
                                                with open(case.age_progressed_image_path, "rb") as image_file:
                                                    b64 = base64.b64encode(image_file.read()).decode("utf-8")
                                                ui.image(f"data:image/jpeg;base64,{b64}").classes("w-24 h-24 rounded object-cover q-mb-xs")
                                            ui.label("Estimated Appearance").classes("text-subtitle2 text-purple-300")
                                            ui.label("AI Model Estimate").classes("text-caption text-slate-500")
                                            
                                        # Citizen submission Sighting
                                        with ui.column().classes("items-center col text-center"):
                                            ui.label("Public Sighting Submission").classes("text-caption text-slate-400")
                                            if sub.image_path and os.path.exists(sub.image_path):
                                                with open(sub.image_path, "rb") as image_file:
                                                    b64 = base64.b64encode(image_file.read()).decode("utf-8")
                                                ui.image(f"data:image/jpeg;base64,{b64}").classes("w-24 h-24 rounded object-cover q-mb-xs")
                                            ui.label(sub.location).classes("text-subtitle2 text-teal-300")
                                            ui.label(sub.submitted_on.strftime('%Y-%m-%d')).classes("text-caption text-slate-500")
                                            
                                    # Form inputs for review
                                    comment_input = ui.input("Reviewer Notes").props("outlined dense placeholder='e.g., Confirmed birthmarks align.'").classes("w-full q-mb-md")
                                    
                                    # Approve/Reject
                                    def review_action(match_id=m.id, status_val="Approved", comm=comment_input):
                                        db_action = db_session()
                                        try:
                                            # Update status
                                            sub_repo.update_sighting_match_status(
                                                db_action, 
                                                match_id=match_id, 
                                                status=status_val, 
                                                reviewed_by=username, 
                                                comments=comm.value
                                            )
                                            
                                            # If approved, update case status to F
                                            rev_match = sub_repo.get_sighting_match(db_action, match_id)
                                            if status_val == "Approved":
                                                case_repo.update_case(db_action, rev_match.case_id, {
                                                    "status": "F", 
                                                    "matched_with": rev_match.submission_id
                                                })
                                                # Mark submission resolved
                                                sub_repo.get_submission_by_id(db_action, rev_match.submission_id).status = "F"
                                                db_action.commit()
                                                
                                                # Trigger notification
                                                target_case = case_repo.get_case_by_id(db_action, rev_match.case_id)
                                                notify_service.notify_complainant_of_match(
                                                    complainant_name=target_case.complainant_name,
                                                    complainant_email=target_case.complainant_email,
                                                    complainant_mobile=target_case.complainant_mobile,
                                                    case_name=target_case.name,
                                                    similarity=rev_match.confidence
                                                )
                                                
                                            ui.notify(f"Match status marked as {status_val}", type="positive")
                                            
                                            # Rerender and refresh stats
                                            render_alerts_list()
                                            render_cases_list()
                                            
                                        except Exception as review_err:
                                            ui.notify(f"Review action failed: {review_err}", type="negative")
                                        finally:
                                            db_session.remove()
                                            
                                    with ui.row().classes("w-full q-col-gutter-sm justify-end"):
                                        ui.button("Reject Sighting", on_click=lambda m_id=m.id, c_in=comment_input: review_action(m_id, "Rejected", c_in)).classes("glass-btn text-red-400")
                                        ui.button("Verify & Approve Sighting", on_click=lambda m_id=m.id, c_in=comment_input: review_action(m_id, "Approved", c_in)).classes("").props("color=green")
                    except Exception as alerts_err:
                        ui.notify(f"Failed to fetch matches: {alerts_err}", type="negative")
                    finally:
                        db_session.remove()

                render_alerts_list()

        # ── TAB 5: CHECK FOR MATCH DASHBOARD ──────────────────────────────────
        def render_match_dashboard():
            # Clear results
            match_results_col.clear()
            db_match = db_session()
            try:
                # Find all pending sighting matches in system
                pending = db_match.query(SightingMatch).filter(SightingMatch.status == "Pending").all()
                if not pending:
                    with match_results_col:
                        ui.label("No pending matches found. Click 'Refresh Match Engine' to check for matches.").classes("text-subtitle2 text-slate-500 q-pa-md w-full text-center")
                    return
                    
                with match_results_col:
                    for m in pending:
                        case = case_repo.get_case_by_id(db_match, m.case_id)
                        sub = sub_repo.get_submission_by_id(db_match, m.submission_id)
                        if not case or not sub:
                            continue
                            
                        with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-lg q-mb-sm"):
                            with ui.row().classes("w-full justify-between items-start q-col-gutter-md"):
                                # Left side details
                                with ui.column().classes("col-12 col-md-6 q-gutter-xs"):
                                    ui.label("Registered Case Profile").classes("text-caption text-blue-300 font-bold")
                                    ui.label(f"Name: {case.name}").classes("text-subtitle1 text-white font-bold")
                                    ui.label(f"Mobile: {case.complainant_mobile or 'N/A'}").classes("text-body2 text-slate-300")
                                    ui.label(f"Age: {case.age}").classes("text-body2 text-slate-300")
                                    ui.label(f"Last Seen: {case.last_seen}").classes("text-body2 text-slate-300")
                                    ui.label(f"Birth Marks: {case.birth_marks or 'N/A'}").classes("text-body2 text-slate-300")
                                    
                                    ui.label("Match Confidence").classes("text-caption text-slate-400 font-bold q-mt-md")
                                    ui.linear_progress(value=m.confidence / 100.0).classes("w-full").props("color=blue track-color=slate-700")
                                    ui.label(f"{m.confidence:.1f}% confidence score").classes("text-caption text-blue-300")
                                    
                                # Right side image & Actions
                                with ui.column().classes("col-12 col-md-6 items-center justify-center text-center"):
                                    if case.original_image_path and os.path.exists(case.original_image_path):
                                        with open(case.original_image_path, "rb") as f:
                                            b64 = base64.b64encode(f.read()).decode("utf-8")
                                        ui.image(f"data:image/jpeg;base64,{b64}").classes("w-32 h-32 rounded object-cover border border-slate-700 q-mb-sm")
                                    else:
                                        ui.icon("account_circle", size="6rem").classes("text-slate-600 q-mb-sm")
                                        
                                    email_container = ui.column().classes("w-full text-left q-mt-sm").style("display: none;")
                                    
                                    # Approve closure handler
                                    async def confirm_match(match_record_id=m.id, c_id=case.id, sub_id=sub.id, email_box=email_container):
                                        db_act = db_session()
                                        try:
                                            # Update Sighting Match Status
                                            match_rec = db_act.query(SightingMatch).filter(SightingMatch.id == match_record_id).first()
                                            if match_rec:
                                                match_rec.status = "Approved"
                                                match_rec.reviewed_by = username
                                                match_rec.reviewed_on = datetime.utcnow()
                                                match_rec.comments = "Match verified via on-demand matcher dashboard."
                                                
                                            # Update Case status to Resolved (Found)
                                            c_rec = db_act.query(RegisteredCases).filter(RegisteredCases.id == c_id).first()
                                            if c_rec:
                                                c_rec.status = "F"
                                                c_rec.matched_with = sub_id
                                                
                                            # Update Sighting status to Found
                                            sub_rec = db_act.query(PublicSubmissions).filter(PublicSubmissions.id == sub_id).first()
                                            if sub_rec:
                                                sub_rec.status = "F"
                                                
                                            db_act.commit()
                                            ui.notify("✅ Status updated. Case is now marked as Found.", type="positive")
                                            
                                            # Send email
                                            notify_service.notify_complainant_of_match(
                                                complainant_name=case.complainant_name,
                                                complainant_email=case.complainant_email,
                                                complainant_mobile=case.complainant_mobile,
                                                case_name=case.name,
                                                similarity=m.confidence
                                            )
                                            ui.notify(f"📧 Notification sent to {case.complainant_email or 'complainant'}", type="info")
                                            
                                            # Show email preview in container
                                            email_box.clear()
                                            with email_box:
                                                ui.label("📬 Generated Email Preview").classes("text-caption text-slate-400 font-bold q-mt-sm")
                                                ui.textarea(
                                                    value=(
                                                        f"To: {case.complainant_email or 'No email'}\n"
                                                        f"Subject: Match Found – {case.name}\n\n"
                                                        f"Hello,\n\n"
                                                        f"A match has been found for the missing person case registered in the system.\n\n"
                                                        f"Case Details:\n"
                                                        f"  Name      : {case.name}\n"
                                                        f"  Age       : {case.age}\n"
                                                        f"  Last Seen : {case.last_seen}\n"
                                                        f"  Case ID   : {case.id}\n\n"
                                                        f"Please log in to the portal to review details."
                                                    )
                                                ).props("outlined readonly").classes("w-full").style("font-size: 11px;")
                                            email_box.style("display: flex;")
                                            
                                            # Refresh lists
                                            render_match_dashboard()
                                            render_alerts_list()
                                            render_cases_list()
                                        except Exception as err:
                                            ui.notify(f"Match confirmation failed: {err}", type="negative")
                                        finally:
                                            db_act.close()
                                            
                                    ui.button("Confirm Match & Resolve Case", icon="check_circle", on_click=confirm_match).classes("w-full").props("color=green size=sm")
                                    email_container.style("display: none;")
                                    email_container.classes("w-full text-left q-mt-sm")
            except Exception as err:
                ui.notify(f"Failed to load matches: {err}", type="negative")
            finally:
                db_match.close()
                
        def trigger_matching_engine():
            loading_spinner.style("display: block;")
            ui.notify("Training KNN model and executing matches...", type="info")
            db_run = db_session()
            try:
                res = match_service.run_face_matching(db_run)
                if res.get("status"):
                    ui.notify(f"Successfully processed matches. Created {res.get('matches_created', 0)} new match entries.", type="positive")
                else:
                    ui.notify(f"Matching completed: {res.get('message', 'No matches found.')}", type="warning")
                render_match_dashboard()
                
                # Update AI match badge count
                btn_alerts.text = f"AI Matches ({len(sub_repo.get_pending_matches(db_run))})"
            except Exception as err:
                ui.notify(f"Matching engine execution failed: {err}", type="negative")
            finally:
                db_run.close()
                loading_spinner.style("display: none;")

        with container_match:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Check for Match").classes("text-h5 text-weight-bold text-white q-mb-xs")
                ui.label("AI-Powered Face Matching Engine (KNN Classifier)").classes("text-caption text-slate-400 q-mb-md")
                
                with ui.row().classes("w-full justify-between items-center q-mb-md"):
                    ui.button("🔄 Refresh Match Engine", on_click=trigger_matching_engine).classes("q-py-sm q-px-md").props("color=blue size=md")
                    loading_spinner = ui.spinner(size="md").classes("q-ml-md").style("display: none;")
                    
                ui.separator().classes("q-mb-md")
                match_results_col = ui.column().classes("w-full q-gutter-md")

        # ── TAB 4: CASE REGISTRATION FORM ──────────────────────────────────────
        with container_register:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Register Missing Person Case File").classes("text-h6 text-weight-bold text-white q-mb-md")
                
                # Demographics
                ui.label("Personal Information").classes("text-subtitle2 text-blue-300 font-bold q-mb-xs")
                name_input = ui.input("Full Name *").props("outlined dense").classes("w-full q-mb-sm")
                father_input = ui.input("Father's Name").props("outlined dense").classes("w-full q-mb-sm")
                age_input = ui.input("Registered Age *").props("outlined dense type=number").classes("w-full q-mb-sm")
                
                # Complainant Details
                ui.label("Complainant / Family Information").classes("text-subtitle2 text-blue-300 font-bold q-mt-sm q-mb-xs")
                comp_name = ui.input("Complainant Name *").props("outlined dense").classes("w-full q-mb-sm")
                comp_mobile = ui.input("Complainant Mobile Number").props("outlined dense mask=##########").classes("w-full q-mb-sm")
                comp_email = ui.input("Complainant Email Address").props("outlined dense").classes("w-full q-mb-sm")
                adhaar_input = ui.input("Aadhaar Card Number (12 digits)").props("outlined dense mask=############").classes("w-full q-mb-sm")
                
                # Geography & Physical Desc
                ui.label("Last Seen Details & Descriptions").classes("text-subtitle2 text-blue-300 font-bold q-mt-sm q-mb-xs")
                last_seen_input = ui.input("Last Seen Location/Place *").props("outlined dense placeholder='e.g., Rishikesh bus stop'").classes("w-full q-mb-sm")
                city_input = ui.input("City *").props("outlined dense placeholder='e.g., Haridwar'").classes("w-full q-mb-sm")
                address_input = ui.input("Residence Address").props("outlined dense").classes("w-full q-mb-sm")
                desc_input = ui.textarea("Physical description details").props("outlined dense placeholder='Height, eye color, last worn clothing'").classes("w-full q-mb-sm")
                birthmark_input = ui.input("Identifying Marks / Birthmarks").props("outlined dense").classes("w-full q-mb-sm")
                medical_input = ui.input("Medical / Psychological conditions (Optional)").props("outlined dense placeholder='e.g., Diabetic, Autism'").classes("w-full q-mb-sm")
                langs_input = ui.input("Languages Spoken (Optional)").props("outlined dense placeholder='e.g., Hindi, Punjabi'").classes("w-full q-mb-md")
                
                # Uploader state storage
                reg_file_data = {
                    "filename": None,
                    "content": None,
                    "preview_b64": None,
                    "box": None,
                    "landmarks": None
                }
                
                def clear_upload():
                    reg_file_data["filename"] = None
                    reg_file_data["content"] = None
                    reg_file_data["preview_b64"] = None
                    reg_file_data["box"] = None
                    reg_file_data["landmarks"] = None
                    update_uploader_ui()
                    
                async def handle_reg_upload(e):
                    try:
                        filename = e.file.name
                        content = await e.file.read()
                        
                        import numpy as np
                        import cv2
                        import base64
                        
                        nparr = np.frombuffer(content, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        if img is None:
                            ui.notify("Invalid image file.", type="negative")
                            return
                            
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        landmarks = match_service.extract_face_mesh_from_frame(img_rgb)
                        
                        if not landmarks:
                            ui.notify("No face detected in the photo. Please use a clearer portrait.", type="negative")
                            return
                            
                        # Bounding box coordinates calculation
                        xs = landmarks[0::3]
                        ys = landmarks[1::3]
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        
                        box = {
                            "left": min_x * 100,
                            "top": min_y * 100,
                            "width": (max_x - min_x) * 100,
                            "height": (max_y - min_y) * 100
                        }
                        
                        b64_str = base64.b64encode(content).decode("utf-8")
                        
                        reg_file_data["filename"] = filename
                        reg_file_data["content"] = content
                        reg_file_data["preview_b64"] = b64_str
                        reg_file_data["box"] = box
                        reg_file_data["landmarks"] = landmarks
                        
                        ui.notify(f"Portrait {filename} staged with face landmarks verified.", type="positive")
                        update_uploader_ui()
                        
                    except Exception as upload_err:
                        ui.notify(f"Image processing failed: {upload_err}", type="negative")

                ui.label("Upload Photo").classes("text-caption text-slate-400 q-mb-xs")
                
                # Custom styled Drag & Drop / Upload Card container matching user mockup
                with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-md q-mb-sm").style("background-color: rgba(255, 255, 255, 0.05);"):
                    with ui.row().classes("items-center justify-start q-gutter-md w-full"):
                        # Hidden native uploader element
                        uploader = ui.upload(on_upload=handle_reg_upload, auto_upload=True).classes("hidden").props("id=reg-uploader")
                        
                        # Custom Trigger Button matching style of screenshot
                        ui.button("Upload", icon="upload", on_click=lambda: ui.run_javascript("document.querySelector('#reg-uploader input[type=file]').click()")).classes("glass-btn text-white").props("color=blue size=sm")
                        
                        # Caption label
                        ui.label("200MB per file • JPG, PNG").classes("text-caption text-slate-400 font-medium")
                        
                file_card_container = ui.column().classes("w-full q-gutter-xs q-mb-sm")
                preview_container = ui.column().classes("w-full items-center justify-center text-center q-mb-md")
                
                def update_uploader_ui():
                    file_card_container.clear()
                    preview_container.clear()
                    
                    if reg_file_data["filename"]:
                        size_kb = len(reg_file_data["content"]) / 1024.0
                        with file_card_container:
                            with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-sm row items-center justify-between").style("display: flex; flex-direction: row;"):
                                with ui.row().classes("items-center q-gutter-sm"):
                                    ui.icon("image", size="1.8rem").classes("text-blue-400")
                                    with ui.column():
                                        ui.label(reg_file_data["filename"]).classes("text-subtitle2 text-white font-bold")
                                        ui.label(f"{size_kb:.1f} KB").classes("text-caption text-slate-500")
                                ui.button(icon="close", on_click=clear_upload).props("flat round dense").classes("text-slate-400 hover:text-white")
                                    
                        if reg_file_data["preview_b64"] and reg_file_data["box"]:
                            box = reg_file_data["box"]
                            with preview_container:
                                with ui.element("div").classes("relative").style("width: 100%; max-width: 320px; aspect-ratio: 3/4; overflow: hidden; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"):
                                    ui.image(f"data:image/jpeg;base64,{reg_file_data['preview_b64']}").classes("w-full h-full object-cover")
                                    ui.html(f'''
                                    <div style="position: absolute; left: {box["left"]}%; top: {box["top"]}%; width: {box["width"]}%; height: {box["height"]}%; border: 2px solid #22c55e; box-sizing: border-box;">
                                        <div style="position: absolute; top: -18px; left: -2px; background-color: #22c55e; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; white-space: nowrap; border-radius: 2px 2px 0 0;">Face detected</div>
                                    </div>
                                    ''')
                
                # Register button
                def process_registration():
                    n = name_input.value
                    f = father_input.value
                    a = age_input.value
                    cn = comp_name.value
                    cm = comp_mobile.value
                    ce = comp_email.value
                    adh = adhaar_input.value
                    ls = last_seen_input.value
                    city = city_input.value
                    addr = address_input.value
                    desc = desc_input.value
                    bm = birthmark_input.value
                    med = medical_input.value
                    lang = langs_input.value
                    
                    if not n or not a or not cn or not ls or not city:
                        ui.notify("Please fill in all required fields marked with *", type="warning")
                        return
                    if not reg_file_data["content"] or not reg_file_data["landmarks"]:
                        ui.notify("Please upload a missing person portrait photograph.", type="warning")
                        return
                        
                    db_reg = db_session()
                    try:
                        case_id = str(uuid4())
                        
                        # Save file
                        filename = f"{case_id}_orig.jpg"
                        dest_path = os.path.join(settings.UPLOAD_DIR, filename)
                        with open(dest_path, "wb") as file_out:
                            file_out.write(reg_file_data["content"])
                            
                        # Use already verified face encodings landmarks
                        landmarks = reg_file_data["landmarks"]
                        
                        # Age Progression model estimation
                        prog_filename = f"{case_id}_prog.jpg"
                        prog_path, prog_landmarks = age_service.generate_age_progression(dest_path, prog_filename)
                        
                        # Create case
                        new_case = RegisteredCases(
                            id=case_id,
                            submitted_by=username,
                            name=n,
                            father_name=f,
                            age=a,
                            complainant_name=cn,
                            complainant_mobile=cm,
                            complainant_email=ce,
                            adhaar_card=adh,
                            last_seen=ls,
                            address=addr or "Not provided",
                            city=city,
                            description=desc,
                            face_mesh=json.dumps(landmarks),
                            status="NF",
                            birth_marks=bm or "None",
                            original_image_path=dest_path,
                            age_progressed_image_path=prog_path,
                            age_progressed_face_mesh=prog_landmarks,
                            medical_info=med,
                            languages_spoken=lang,
                            physical_description=desc
                        )
                        case_repo.create_case(db_reg, new_case)
                        
                        # Auto match sightings
                        match_service.run_face_matching(db_reg)
                        
                        # Add initial RAG document context representing the initial case report details
                        initial_context = f"Initial Case Alert: Missing person {n}, age {a}. Last seen at {ls} in {city}. Father name is {f or 'N/A'}. Physical features: {desc or 'N/A'}. Birthmarks: {bm or 'None'}."
                        initial_doc = InvestigationDoc(
                            case_id=case_id,
                            doc_type="Initial Case Details",
                            title="Registration Demographics",
                            content=initial_context
                        )
                        db_reg.add(initial_doc)
                        db_reg.commit()
                        
                        ui.notify("Case successfully registered! AI age progression generated and matches updated.", type="positive")
                        
                        # Reset inputs
                        name_input.value = ""
                        father_input.value = ""
                        age_input.value = ""
                        comp_name.value = ""
                        comp_mobile.value = ""
                        comp_email.value = ""
                        adhaar_input.value = ""
                        last_seen_input.value = ""
                        city_input.value = ""
                        address_input.value = ""
                        desc_input.value = ""
                        birthmark_input.value = ""
                        medical_input.value = ""
                        langs_input.value = ""
                        clear_upload()
                        
                        # Show case timeline overview
                        ui.navigate.to(f"/cases/{case_id}")
                    except Exception as e:
                        ui.notify(f"Registration failed: {e}", type="negative")
                    finally:
                        db_session.remove()
                        
                ui.button("Confirm Profile Registration", on_click=process_registration).classes("w-full").props("color=blue")

        # Set default tab overview map load
        show_tab("Dashboard")
