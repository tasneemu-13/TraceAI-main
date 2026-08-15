from nicegui import ui, app
from app.frontend import layout
from app.database import db_session
from app.repositories import user as user_repo
from app.services import auth as auth_service

def content():
    """
    Renders the beautiful glassmorphic login screen.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Redirect if already logged in
    if app.storage.user.get("user"):
        ui.navigate.to("/officer")
        return
        
    with ui.column().classes("w-full items-center justify-center q-pt-xl q-px-md"):
        with ui.card().classes("glass-card q-pa-xl w-full").style("max-width: 460px;"):
            
            # Header
            with ui.column().classes("w-full items-center justify-center q-mb-md text-center"):
                ui.icon("fingerprint", size="3rem").classes("text-blue-500 q-mb-xs")
                ui.label("Secure Access Portal").classes("text-h5 text-weight-bold text-white")
                ui.label("Sign in to continue to TraceAI").classes("text-caption text-slate-400")
            
            # Tab Selector (for citizen, officer, admin)
            selected_role = {"value": "Officer"}  # Default tab
            
            with ui.row().classes("w-full justify-between q-mb-md q-col-gutter-xs"):
                btn_public = ui.button("Public", on_click=lambda: set_role("Public")).classes("col glass-btn")
                btn_officer = ui.button("Officer", on_click=lambda: set_role("Officer")).classes("col glass-btn text-blue-400")
                btn_admin = ui.button("Admin", on_click=lambda: set_role("Admin")).classes("col glass-btn")
                
            def set_role(role_name: str):
                selected_role["value"] = role_name
                # Reset highlights
                btn_public.classes(remove="text-blue-400 text-purple-400 text-teal-400")
                btn_officer.classes(remove="text-blue-400 text-purple-400 text-teal-400")
                btn_admin.classes(remove="text-blue-400 text-purple-400 text-teal-400")
                
                if role_name == "Public":
                    btn_public.classes("text-teal-400")
                elif role_name == "Officer":
                    btn_officer.classes("text-blue-400")
                else:
                    btn_admin.classes("text-purple-400")
                    
                role_label.text = f"Role: {role_name} Portal"
                
            role_label = ui.label("Role: Officer Portal").classes("text-caption text-blue-300 text-weight-bold q-mb-sm text-center w-full")
            
            # Input Fields
            username_input = ui.input("Username").props("outlined dense square").classes("w-full q-mb-sm")
            password_input = ui.input("Password").props("outlined dense square type=password").classes("w-full q-mb-md")
            
            # Remember me & Forgot Password
            with ui.row().classes("w-full justify-between items-center q-mb-md"):
                ui.checkbox("Remember Me").props("dense").classes("text-caption text-slate-400")
                ui.label("Forgot Password?").classes("text-caption text-blue-400 cursor-pointer").on("click", lambda: forgot_password_dialog.open())
                
            def try_login():
                uname = username_input.value
                pwd = password_input.value
                role = selected_role["value"]
                
                if not uname or not pwd:
                    ui.notify("Please fill in all fields", type="warning")
                    return
                    
                db = db_session()
                try:
                    db_user = user_repo.get_user_by_username(db, uname)
                    if not db_user or not auth_service.verify_password(pwd, db_user.hashed_password):
                        ui.notify("Incorrect username or password", type="negative")
                        return
                        
                    # Verify user role matches selection
                    if db_user.role != role:
                        ui.notify(f"Access Denied: Account is not registered as {role}", type="negative")
                        return
                        
                    # Set session store variables
                    app.storage.user["user"] = db_user.username
                    app.storage.user["role"] = db_user.role
                    app.storage.user["name"] = db_user.name
                    
                    ui.notify(f"Welcome back, {db_user.name}!", type="positive")
                    
                    # Redirection
                    if db_user.role == "Admin":
                        ui.navigate.to("/admin")
                    else:
                        ui.navigate.to("/officer")
                except Exception as e:
                    ui.notify(f"System Error: {e}", type="negative")
                finally:
                    db_session.remove()
                    
            ui.button("Sign In", on_click=try_login).classes("w-full q-py-sm text-weight-bold").props("color=blue")
            
            # Citizen Registration quick link
            with ui.row().classes("w-full justify-center q-mt-md"):
                ui.label("Citizen with no account?").classes("text-caption text-slate-400 q-mr-xs")
                ui.label("Register Sighting Anonymously").classes("text-caption text-teal-400 cursor-pointer text-weight-bold").on("click", lambda: ui.navigate.to("/public"))

    # Forgot Password Dialog Flow
    with ui.dialog() as forgot_password_dialog, ui.card().classes("glass-card q-pa-lg").style("min-width: 380px;"):
        ui.label("Reset Password").classes("text-h6 text-weight-bold text-white q-mb-xs")
        ui.label("Enter your registered email to receive an OTP.").classes("text-caption text-slate-400 q-mb-md")
        
        email_field = ui.input("Email Address").props("outlined dense").classes("w-full q-mb-md")
        otp_field = ui.input("OTP Code").props("outlined dense").classes("w-full q-mb-sm").style("display: none;")
        new_pw_field = ui.input("New Password").props("outlined dense type=password").classes("w-full q-mb-md").style("display: none;")
        
        # State trackers for the password reset sequence
        state = {"step": 1, "otp_sent": None}
        
        def handle_reset_flow():
            email_val = email_field.value
            db = db_session()
            try:
                if state["step"] == 1:
                    # Step 1: Send OTP
                    if not email_val:
                        ui.notify("Please enter your email", type="warning")
                        return
                    db_user = user_repo.get_user_by_email(db, email_val)
                    if not db_user:
                        ui.notify("Email address not found", type="negative")
                        return
                        
                    otp = auth_service.generate_otp()
                    auth_service.store_otp(db_user.email, otp)
                    sent = auth_service.send_email(
                        db_user.email,
                        "TraceAI - Password Reset OTP",
                        f"Your verification code is: {otp}. This code is valid for 5 minutes."
                    )
                    
                    # Transition to step 2 inputs
                    state["step"] = 2
                    email_field.disable()
                    otp_field.style("display: block;")
                    new_pw_field.style("display: block;")
                    action_btn.text = "Confirm Reset"
                    
                    if sent:
                        ui.notify("OTP code sent to email.", type="positive")
                    else:
                        otp_field.value = otp
                        ui.notify(f"[Dev Mode] SMTP not configured. Staged OTP: {otp}", type="warning", duration=15)
                else:
                    # Step 2: Validate OTP and reset password
                    otp_val = otp_field.value
                    new_pw_val = new_pw_field.value
                    if not otp_val or not new_pw_val:
                        ui.notify("Please fill in OTP and new password", type="warning")
                        return
                        
                    db_user = user_repo.get_user_by_email(db, email_val)
                    if not auth_service.verify_otp(db_user.email, otp_val):
                        ui.notify("Invalid or expired OTP", type="negative")
                        return
                        
                    ok, msg = auth_service.validate_password_strength(new_pw_val)
                    if not ok:
                        ui.notify(msg, type="warning")
                        return
                        
                    # Update DB
                    user_repo.update_user(db, db_user, {"hashed_password": auth_service.hash_password(new_pw_val)})
                    ui.notify("Password successfully reset. You can now login.", type="positive")
                    forgot_password_dialog.close()
            except Exception as e:
                ui.notify(f"Reset failed: {e}", type="negative")
            finally:
                db_session.remove()
                
        action_btn = ui.button("Send Verification Code", on_click=handle_reset_flow).classes("w-full").props("color=blue")
        ui.button("Cancel", on_click=lambda: forgot_password_dialog.close()).classes("w-full glass-btn q-mt-xs")
