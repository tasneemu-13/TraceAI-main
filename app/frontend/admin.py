import os
import shutil
import requests
from datetime import datetime
from nicegui import ui, app
from app.frontend import layout
from app.database import db_session, engine
from app.repositories import user as user_repo
from app.models.user import User
from app.services import auth as auth_service
from app.models.case import RegisteredCases
from app.models.doc import InvestigationDoc, SightingMatch
from app.repositories import case as case_repo
from app.repositories import submission as sub_repo
from collections import defaultdict

def content():
    """
    Renders the platform administrator dashboard.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Auth verification
    username = app.storage.user.get("user")
    role = app.storage.user.get("role")
    if not username or role != "Admin":
        ui.navigate.to("/login")
        return

    # Diagnostic checks
    db_status = "Online"
    try:
        conn = engine.connect()
        conn.close()
    except Exception:
        db_status = "Offline"
        
    ollama_status = "Online"
    ollama_models = []
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            ollama_models = [m["name"] for m in res.json().get("models", [])]
        else:
            ollama_status = f"Offline ({res.status_code})"
    except Exception:
        ollama_status = "Offline (Connection Refused)"

    with ui.column().classes("w-full q-pa-md"):
        # Header banner
        with ui.column().classes("q-mb-md"):
            ui.label("TraceAI Platform Administration").classes("text-h4 text-weight-bold text-white")
            ui.label("Control station, user databases, health monitoring, and RAG configuration").classes("text-caption text-slate-400")

        # Split dashboard panels
        with ui.row().classes("w-full q-col-gutter-md"):
            # LEFT: User Management
            with ui.column().classes("col-12 col-md-7 q-gutter-md"):
                with ui.card().classes("w-full glass-card q-pa-lg"):
                    ui.label("User Account Management").classes("text-h6 text-weight-bold text-white q-mb-xs")
                    ui.label("View and provision accounts for station officers and admins.").classes("text-caption text-slate-400 q-mb-md")
                    
                    user_list_col = ui.column().classes("w-full q-gutter-xs q-mb-md")
                    
                    def render_users():
                        user_list_col.clear()
                        db_conn = db_session()
                        try:
                            users = user_repo.list_users(db_conn)
                            with user_list_col:
                                for u in users:
                                    with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-sm row items-center justify-between").style("display:flex; flex-direction:row;"):
                                        with ui.row().classes("items-center q-gutter-sm"):
                                            ui.icon("account_circle", size="2.5rem").classes("text-blue-400")
                                            with ui.column():
                                                ui.label(f"{u.name} (@{u.username})").classes("text-subtitle2 text-white")
                                                ui.label(f"Email: {u.email} | City: {u.city}").classes("text-caption text-slate-500")
                                        with ui.row().classes("items-center q-gutter-xs"):
                                            role_color = "red" if u.role == "Admin" else ("blue" if u.role == "Officer" else "teal")
                                            ui.badge(u.role, color=role_color)
                                            # Verification action
                                            if not u.is_verified:
                                                def verify_usr(user_id=u.id):
                                                    db_usr_act = db_session()
                                                    db_u = user_repo.get_user_by_id(db_usr_act, user_id)
                                                    user_repo.update_user(db_usr_act, db_u, {"is_verified": True})
                                                    ui.notify("User successfully verified", type="positive")
                                                    render_users()
                                                    db_session.remove()
                                                ui.button("Verify", on_click=verify_usr).classes("glass-btn text-teal-300").props("dense size=xs")
                        except Exception as e:
                            ui.notify(f"Failed to fetch users: {e}", type="negative")
                        finally:
                            db_session.remove()
                            
                    render_users()
                    
                    # Provision New Officer Form
                    ui.label("Provision New Station Officer").classes("text-subtitle2 text-blue-300 font-bold q-mt-md q-mb-xs")
                    with ui.row().classes("w-full q-col-gutter-xs q-mb-sm"):
                        o_name = ui.input("Full Name").props("outlined dense").classes("col-12 col-sm-6")
                        o_uname = ui.input("Username").props("outlined dense").classes("col-12 col-sm-6")
                    with ui.row().classes("w-full q-col-gutter-xs q-mb-sm"):
                        o_email = ui.input("Email").props("outlined dense").classes("col-12 col-sm-6")
                        o_pass = ui.input("Password").props("outlined dense type=password").classes("col-12 col-sm-6")
                    with ui.row().classes("w-full q-col-gutter-xs q-mb-md"):
                        o_city = ui.input("City").props("outlined dense").classes("col-12 col-sm-6")
                        o_area = ui.input("Area").props("outlined dense").classes("col-12 col-sm-6")
                        
                    def register_officer():
                        name, uname, email, pw, city, area = o_name.value, o_uname.value, o_email.value, o_pass.value, o_city.value, o_area.value
                        if not all([name, uname, email, pw, city]):
                            ui.notify("Please fill in name, username, email, password, and city", type="warning")
                            return
                            
                        db_prov = db_session()
                        try:
                            if user_repo.get_user_by_username(db_prov, uname):
                                ui.notify("Username already taken", type="negative")
                                return
                            new_officer = User(
                                name=name,
                                username=uname,
                                email=email,
                                hashed_password=auth_service.hash_password(pw),
                                role="Officer",
                                city=city,
                                area=area or "HQ",
                                is_verified=True
                            )
                            user_repo.create_user(db_prov, new_officer)
                            ui.notify("Officer provisioned successfully!", type="positive")
                            # Reset inputs
                            o_name.value = ""
                            o_uname.value = ""
                            o_email.value = ""
                            o_pass.value = ""
                            o_city.value = ""
                            o_area.value = ""
                            render_users()
                        except Exception as prov_err:
                            ui.notify(f"Provisioning failed: {prov_err}", type="negative")
                        finally:
                            db_session.remove()
                            
                    ui.button("Provision Officer Account", on_click=register_officer).classes("w-full").props("color=blue size=sm")

            # RIGHT: Diagnostic Health Checks
            with ui.column().classes("col-12 col-md-5 q-gutter-md"):
                with ui.card().classes("w-full glass-card q-pa-lg"):
                    ui.label("System Diagnostics").classes("text-h6 text-weight-bold text-white q-mb-md")
                    
                    with ui.column().classes("w-full q-gutter-sm"):
                        def diagnostic_row(label, status_val, status_color):
                            with ui.row().classes("w-full justify-between items-center"):
                                ui.label(label).classes("text-caption text-slate-400")
                                ui.badge(status_val, color=status_color)
                                
                        diagnostic_row("MySQL Database Service", db_status, "green" if db_status == "Online" else "red")
                        diagnostic_row("Local Cache (Redis/Fakeredis)", "Running (Mock)", "green")
                        diagnostic_row("Ollama LLM Server", ollama_status, "green" if ollama_status == "Online" else "red")
                        
                        # Filesystem size
                        disk_usage = shutil.disk_usage(".")
                        free_gb = disk_usage.free / (1024 ** 3)
                        diagnostic_row("Local Storage Capacity", f"{free_gb:.1f} GB Free", "blue")
                        
                with ui.card().classes("w-full glass-card q-pa-lg"):
                    ui.label("AI Engine & Model Status").classes("text-h6 text-weight-bold text-white q-mb-md")
                    
                    with ui.column().classes("w-full q-gutter-sm text-sm"):
                        with ui.row().classes("w-full justify-between"):
                            ui.label("Facial Landmarker:").classes("text-slate-400")
                            ui.label("MediaPipe Task 1.0").classes("text-white font-bold")
                        with ui.row().classes("w-full justify-between"):
                            ui.label("KNN Classification:").classes("text-slate-400")
                            ui.label("BallTree Weight-Distance").classes("text-white font-bold")
                        with ui.row().classes("w-full justify-between"):
                            ui.label("Age Progression Model:").classes("text-slate-400")
                            ui.label("SD-Img2Img / OpenCV Filter").classes("text-white font-bold")
                        with ui.row().classes("w-full justify-between"):
                            ui.label("RAG LLM Engine:").classes("text-slate-400")
                            ui.label("Llama 3 (Ollama)").classes("text-white font-bold")
                            
                        # Listed Models in Ollama
                        ui.label("Ollama Models Loaded:").classes("text-caption text-purple-300 font-bold q-mt-md")
                        if ollama_models:
                            for m in ollama_models:
                                ui.label(f"• {m}").classes("text-white q-pl-sm")
                        else:
                            ui.label("No active models detected on local host (check connection).").classes("text-slate-500 q-pl-sm italic")
                            
                with ui.card().classes("w-full glass-card q-pa-lg"):
                    ui.label("SMTP Mail Configurations").classes("text-h6 text-weight-bold text-white q-mb-xs")
                    ui.label("Configure SMTP relay for live email OTP verification.").classes("text-caption text-slate-400 q-mb-md")
                    
                    import json
                    config_file = "smtp_config.json"
                    current_host = ""
                    current_port = "587"
                    current_user = ""
                    current_pass = ""
                    if os.path.exists(config_file):
                        try:
                            with open(config_file, "r") as f:
                                cfg = json.load(f)
                                current_host = cfg.get("SMTP_HOST", "")
                                current_port = cfg.get("SMTP_PORT", "587")
                                current_user = cfg.get("SMTP_USER", "")
                                current_pass = cfg.get("SMTP_PASSWORD", "")
                        except Exception:
                            pass
                            
                    smtp_host_in = ui.input("SMTP Host", value=current_host).props("outlined dense").classes("w-full q-mb-xs")
                    smtp_port_in = ui.input("SMTP Port", value=current_port).props("outlined dense").classes("w-full q-mb-xs")
                    smtp_user_in = ui.input("SMTP Username", value=current_user).props("outlined dense").classes("w-full q-mb-xs")
                    smtp_pass_in = ui.input("SMTP Password", value=current_pass).props("outlined dense type=password").classes("w-full q-mb-md")
                    
                    def save_smtp():
                        host = smtp_host_in.value
                        port = smtp_port_in.value
                        user = smtp_user_in.value
                        pwd = smtp_pass_in.value
                        
                        cfg_data = {
                            "SMTP_HOST": host,
                            "SMTP_PORT": port,
                            "SMTP_USER": user,
                            "SMTP_PASSWORD": pwd
                        }
                        try:
                            with open(config_file, "w") as f_out:
                                json.dump(cfg_data, f_out, indent=2)
                            ui.notify("SMTP Configuration saved successfully!", type="positive")
                        except Exception as e:
                            ui.notify(f"Save failed: {e}", type="negative")
                            
                    ui.button("Save Configuration", on_click=save_smtp).classes("w-full").props("color=blue size=sm")

        # ── Registered Case Management & Data Deduplication Panel ──────────────
        ui.separator().classes("q-my-md")
        
        with ui.card().classes("w-full glass-card q-pa-lg q-mt-md"):
            ui.label("Registered Case Management").classes("text-h6 text-weight-bold text-white q-mb-xs")
            ui.label("Review active case files, filter duplicate registrations, and delete obsolete entries.").classes("text-caption text-slate-400 q-mb-md")
            
            show_dup_only = ui.checkbox("Show duplicate registrations only", value=False)
            
            cases_admin_col = ui.column().classes("w-full q-gutter-sm")
            
            def render_cases():
                cases_admin_col.clear()
                db = db_session()
                try:
                    cases = db.query(RegisteredCases).all()
                    if not cases:
                        with cases_admin_col:
                            ui.label("No registered cases found in the system.").classes("text-subtitle2 text-slate-500 q-pa-md w-full text-center")
                        return
                        
                    # Group by name (lowercase), age, and city to find duplicates
                    groups = defaultdict(list)
                    for c in cases:
                        key = (c.name.strip().lower(), str(c.age), c.city.strip().lower() if c.city else "")
                        groups[key].append(c)
                        
                    dup_case_ids = set()
                    for key, val in groups.items():
                        if len(val) > 1:
                            for v in val:
                                dup_case_ids.add(v.id)
                                
                    cases_to_show = [c for c in cases if c.id in dup_case_ids] if show_dup_only.value else cases
                    
                    if not cases_to_show:
                        with cases_admin_col:
                            ui.label("No cases match the selected duplicates filter.").classes("text-subtitle2 text-slate-500 q-pa-md w-full text-center")
                        return
                        
                    with cases_admin_col:
                        for c in cases_to_show:
                            is_dup = c.id in dup_case_ids
                            border_color = "rgba(239, 68, 68, 0.3)" if is_dup else "rgba(255, 255, 255, 0.05)"
                            bg_class = "w-full bg-slate-900 border q-pa-sm row items-center justify-between"
                            
                            with ui.card().classes(bg_class).style(f"display: flex; flex-direction: row; border-color: {border_color};"):
                                with ui.row().classes("items-center q-gutter-md"):
                                    if is_dup:
                                        ui.badge("DUPLICATE", color="red")
                                    with ui.column():
                                        ui.label(c.name).classes("text-subtitle2 text-white font-bold")
                                        ui.label(f"Age: {c.age} | City: {c.city or 'N/A'} | Registered by: @{c.submitted_by}").classes("text-caption text-slate-400")
                                        ui.label(f"Aadhaar: {c.adhaar_card or 'N/A'} | Date: {c.submitted_on.strftime('%Y-%m-%d')}").classes("text-caption text-slate-500")
                                        
                                with ui.row().classes("items-center q-gutter-sm"):
                                    
                                    async def trigger_delete(c_id=c.id, c_name=c.name):
                                        # Open a NiceGUI modal dialog to confirm deletion
                                        with ui.dialog() as dialog, ui.card().classes("glass-card q-pa-lg").style("min-width: 400px;"):
                                            ui.label("Confirm Delete Registered Case").classes("text-h6 text-weight-bold text-white q-mb-xs")
                                            ui.label(f"Are you sure you want to permanently delete case file for {c_name}? This action is irreversible and will delete all associated sightings and notes.").classes("text-body2 text-slate-300 q-mb-md")
                                            
                                            with ui.row().classes("w-full justify-end q-gutter-sm"):
                                                ui.button("Cancel", on_click=dialog.close).classes("glass-btn")
                                                
                                                async def process_del(target_id=c_id):
                                                    db_del = db_session()
                                                    try:
                                                        case_to_del = db_del.query(RegisteredCases).filter(RegisteredCases.id == target_id).first()
                                                        if case_to_del:
                                                            # Delete physical portrait image files
                                                            if case_to_del.original_image_path and os.path.exists(case_to_del.original_image_path):
                                                                try:
                                                                    os.remove(case_to_del.original_image_path)
                                                                except Exception:
                                                                    pass
                                                            if case_to_del.age_progressed_image_path and os.path.exists(case_to_del.age_progressed_image_path):
                                                                try:
                                                                    os.remove(case_to_del.age_progressed_image_path)
                                                                except Exception:
                                                                    pass
                                                            
                                                            # Delete matches
                                                            db_del.query(SightingMatch).filter(SightingMatch.case_id == target_id).delete()
                                                            # Delete docs
                                                            db_del.query(InvestigationDoc).filter(InvestigationDoc.case_id == target_id).delete()
                                                            
                                                            db_del.delete(case_to_del)
                                                            db_del.commit()
                                                            
                                                            ui.notify(f"Case for {c_name} deleted successfully.", type="positive")
                                                            render_cases()
                                                        else:
                                                            ui.notify("Case not found.", type="negative")
                                                    except Exception as del_exc:
                                                        ui.notify(f"Delete failed: {del_exc}", type="negative")
                                                    finally:
                                                        db_del.close()
                                                        dialog.close()
                                                        
                                                ui.button("Confirm Delete", on_click=process_del).props("color=red")
                                        dialog.open()
                                        
                                    ui.button("Delete Case", icon="delete", on_click=trigger_delete).classes("glass-btn text-red-400").props("dense size=sm")
                except Exception as err:
                    ui.notify(f"Failed to fetch cases: {err}", type="negative")
                finally:
                    db.close()
            
            show_dup_only.on_value_change(lambda: render_cases())
            render_cases()
