import os
import json
import base64
from datetime import datetime
from uuid import uuid4
from nicegui import ui, app
from app.frontend import layout
from app.database import db_session
from app.repositories import submission as sub_repo
from app.repositories import case as case_repo
from app.models.submission import PublicSubmissions
from app.models.case import RegisteredCases
from app.services import matching as match_service
from app.config import settings

def content():
    """
    Renders the public citizen submission and tracking portal.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Active tab state
    active_tab = {"value": "Report"}
    
    with ui.column().classes("w-full items-center q-pt-lg q-px-md"):
        # Top banner
        with ui.column().classes("items-center text-center q-mb-md"):
            ui.icon("diversity_1", size="3rem").classes("text-teal-400 q-mb-xs")
            ui.label("Citizen Help & Report Center").classes("text-h4 text-weight-bold text-white")
            ui.label("Submit sighting clues anonymously or track existing submissions").classes("text-caption text-slate-400")
            
        # Tab bar selector
        with ui.row().classes("w-full max-w-4xl justify-center q-mb-md"):
            with ui.card().classes("glass-card row w-full justify-around q-col-gutter-xs q-pa-sm"):
                btn_report = ui.button("Report a Sighting", icon="photo_camera", on_click=lambda: show_tab("Report")).classes("col glass-btn text-teal-400")
                btn_track = ui.button("Track My Report", icon="gps_fixed", on_click=lambda: show_tab("Track")).classes("col glass-btn")
                btn_search = ui.button("Search Missing Persons", icon="search", on_click=lambda: show_tab("Search")).classes("col glass-btn")
                
        # Main containers
        container_report = ui.column().classes("w-full max-w-2xl items-center q-gutter-md")
        container_track = ui.column().classes("w-full max-w-2xl items-center q-gutter-md").style("display: none;")
        container_search = ui.column().classes("w-full max-w-4xl items-center q-gutter-md").style("display: none;")
        
        def show_tab(tab_name: str):
            active_tab["value"] = tab_name
            
            # Button highlights
            btn_report.classes(remove="text-teal-400")
            btn_track.classes(remove="text-teal-400")
            btn_search.classes(remove="text-teal-400")
            
            container_report.style("display: none;")
            container_track.style("display: none;")
            container_search.style("display: none;")
            
            if tab_name == "Report":
                btn_report.classes("text-teal-400")
                container_report.style("display: flex;")
            elif tab_name == "Track":
                btn_track.classes("text-teal-400")
                container_track.style("display: flex;")
            else:
                btn_search.classes("text-teal-400")
                container_search.style("display: flex;")

        # ── TAB 1: REPORT SIGHTING ─────────────────────────────────────────────
        with container_report:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Submit Location & Details").classes("text-h6 text-weight-bold text-white q-mb-md")
                
                # Image/Video Selector
                mode_selector = ui.radio(["Photo Upload", "Video Upload"], value="Photo Upload").props("inline").classes("q-mb-md text-slate-300")
                
                # Form Fields
                citizen_name = ui.input("Your Name (Optional)").props("outlined dense").classes("w-full q-mb-sm").tooltip("Leave blank to submit anonymously")
                citizen_mobile = ui.input("Your Contact Mobile *").props("outlined dense mask=##########").classes("w-full q-mb-sm")
                citizen_email = ui.input("Your Email (Optional)").props("outlined dense").classes("w-full q-mb-sm")
                sighting_loc = ui.input("Sighting Location *").props("outlined dense placeholder='e.g., Haridwar Ghat near temple'").classes("w-full q-mb-sm")
                
                # GPS Captures
                with ui.row().classes("w-full items-center justify-between q-mb-sm"):
                    gps_label = ui.label("GPS Location: Not captured").classes("text-caption text-slate-400")
                    ui.button("Capture Live GPS", icon="my_location", on_click=lambda: capture_gps()).classes("glass-btn text-teal-300").props("dense size=sm")
                
                lat_input = ui.number("Latitude", format="%.6f").classes("w-full q-mb-xs").props("outlined dense").style("display:none;")
                lon_input = ui.number("Longitude", format="%.6f").classes("w-full q-mb-xs").props("outlined dense").style("display:none;")
                
                # GPS Capturing Javascript
                async def capture_gps():
                    gps_label.text = "Fetching coordinates..."
                    # NiceGUI JS execution to retrieve user location
                    coords = await ui.run_javascript('''
                        new Promise((resolve, reject) => {
                            if (!navigator.geolocation) {
                                resolve(null);
                            }
                            navigator.geolocation.getCurrentPosition(
                                (pos) => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                                (err) => resolve(null),
                                {timeout: 8000}
                            );
                        });
                    ''')
                    if coords:
                        lat_input.value = coords["lat"]
                        lon_input.value = coords["lon"]
                        gps_label.text = f"GPS Coordinates: {coords['lat']:.5f}, {coords['lon']:.5f}"
                        ui.notify("GPS Coordinates captured successfully", type="positive")
                    else:
                        gps_label.text = "GPS: Permission Denied or Timeout."
                        ui.notify("Could not capture GPS. Please input location details manually.", type="warning")
                
                desc_input = ui.textarea("Physical Description / What were they wearing?").props("outlined placeholder='Height, clothes color, marks'").classes("w-full q-mb-md")
                
                # File Uploader
                # In NiceGUI, we upload files using a base64 encoder or local files.
                # A file uploader element is extremely standard
                uploaded_file_data = {"filename": None, "content": None}
                
                async def handle_upload(e):
                    uploaded_file_data["filename"] = e.file.name
                    uploaded_file_data["content"] = await e.file.read()
                    ui.notify(f"File {e.file.name} staged for upload.", type="info")
                    file_badge.text = f"Staged: {e.file.name}"
                    
                ui.upload(on_upload=handle_upload, label="Take photo / Upload file", auto_upload=True).classes("w-full q-mb-sm")
                file_badge = ui.label("No file selected").classes("text-caption text-slate-500 q-mb-md")
                
                # Submission trigger
                def process_sighting_submit():
                    name_val = citizen_name.value
                    mobile_val = citizen_mobile.value
                    email_val = citizen_email.value
                    loc_val = sighting_loc.value
                    lat_val = lat_input.value
                    lon_val = lon_input.value
                    desc_val = desc_input.value
                    mode_val = mode_selector.value
                    
                    if not mobile_val or len(mobile_val) != 10:
                        ui.notify("Valid 10-digit mobile number is required for alerts.", type="warning")
                        return
                    if not loc_val:
                        ui.notify("Location details are required.", type="warning")
                        return
                    if not uploaded_file_data["content"]:
                        ui.notify("Please upload or capture a photo/video file first.", type="warning")
                        return
                        
                    # Save Sighting
                    db = db_session()
                    try:
                        sub_id = str(uuid4())
                        
                        # Save file to disk
                        ext = uploaded_file_data["filename"].split(".")[-1]
                        filename = f"{sub_id}.{ext}"
                        dest_path = os.path.join(settings.UPLOAD_DIR, filename)
                        with open(dest_path, "wb") as f:
                            f.write(uploaded_file_data["content"])
                            
                        # Extracted landmarks
                        landmarks = None
                        if "photo" in mode_val.lower():
                            import cv2
                            img_cv = cv2.imread(dest_path)
                            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                            landmarks = match_service.extract_face_mesh_from_frame(img_rgb)
                            
                            if not landmarks:
                                if os.path.exists(dest_path):
                                    os.remove(dest_path)
                                ui.notify("No face detected in the photo. Please use a clearer portrait.", type="negative")
                                return
                                
                            # Register submission
                            new_sub = PublicSubmissions(
                                id=sub_id,
                                submitted_by=name_val or "Anonymous",
                                face_mesh=json.dumps(landmarks),
                                location=loc_val,
                                mobile=mobile_val,
                                email=email_val,
                                status="NF",
                                image_path=dest_path,
                                is_anonymous=(not bool(name_val)),
                                latitude=lat_val,
                                longitude=lon_val,
                                description=desc_val
                            )
                            sub_repo.create_submission(db, new_sub)
                            match_service.run_face_matching(db)
                            ui.notify("Sighting report successfully uploaded. AI face encodings matching in background.", type="positive")
                            
                            # Success card display
                            success_dialog(sub_id)
                        else:
                            # Video Mode
                            try:
                                ui.notify("Extracting faces from video frames...", type="info")
                                extracted_faces = match_service.extract_unique_faces_from_video(dest_path)
                            except Exception as video_err:
                                ui.notify(f"Video reading failed: {video_err}", type="negative")
                                return
                            finally:
                                # Keep video or delete? Let's keep it linked.
                                pass
                                
                            if not extracted_faces:
                                ui.notify("No unique faces detected in the video.", type="negative")
                                return
                                
                            created_ids = []
                            for idx, (lms, frame_rgb) in enumerate(extracted_faces):
                                f_id = str(uuid4())
                                f_filename = f"{f_id}_v{idx}.jpg"
                                f_dest_path = os.path.join(settings.UPLOAD_DIR, f_filename)
                                import PIL.Image
                                PIL.Image.fromarray(frame_rgb).save(f_dest_path)
                                
                                new_sub = PublicSubmissions(
                                    id=f_id,
                                    submitted_by=name_val or "Anonymous",
                                    face_mesh=json.dumps(lms),
                                    location=loc_val,
                                    mobile=mobile_val,
                                    email=email_val,
                                    status="NF",
                                    image_path=f_dest_path,
                                    video_path=dest_path,
                                    is_anonymous=(not bool(name_val)),
                                    latitude=lat_val,
                                    longitude=lon_val,
                                    description=desc_val
                                )
                                sub_repo.create_submission(db, new_sub)
                                created_ids.append(f_id)
                                
                            match_service.run_face_matching(db)
                            ui.notify(f"Successfully processed video. Registered {len(created_ids)} unique sightings.", type="positive")
                            success_dialog(created_ids[0])
                    except Exception as e:
                        ui.notify(f"Submission failed: {e}", type="negative")
                    finally:
                        db_session.remove()
                        
                ui.button("Submit Report", on_click=process_sighting_submit).classes("w-full text-weight-bold q-py-sm").props("color=teal")

        # ── TAB 2: TRACK SIGHTING ──────────────────────────────────────────────
        with container_track:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Track Sighting Case").classes("text-h6 text-weight-bold text-white q-mb-sm")
                ui.label("Input your 36-character unique sighting reference ID to check matching progress.").classes("text-caption text-slate-400 q-mb-md")
                
                track_id_input = ui.input("Sighting Reference ID").props("outlined dense placeholder='e.g., d54fa98f-...'").classes("w-full q-mb-md")
                
                tracking_results = ui.column().classes("w-full items-center q-pt-md")
                
                def search_tracking():
                    tid = track_id_input.value.strip()
                    if not tid:
                        ui.notify("Please enter a valid sighting ID", type="warning")
                        return
                    
                    db = db_session()
                    try:
                        sub = sub_repo.get_submission_by_id(db, tid)
                        if not sub:
                            ui.notify("No sighting record matches this ID", type="negative")
                            tracking_results.clear()
                            return
                            
                        # Resolve status timeline
                        matches = sub_repo.get_sighting_matches_by_submission(db, tid)
                        v_status = "Under AI Verification"
                        match_case = "Pending Verification"
                        
                        for m in matches:
                            if m.status == "Approved":
                                v_status = "Verified Match"
                                case = case_repo.get_case_by_id(db, m.case_id)
                                if case:
                                    match_case = f"Successfully matched with Registered Profile of {case.name}"
                            elif m.status == "Rejected" and v_status != "Verified Match":
                                v_status = "Match Disproved"
                                match_case = "Encodings do not match target features"
                                
                        # Clear and build tracking view
                        tracking_results.clear()
                        with tracking_results:
                            with ui.card().classes("w-full q-pa-md glass-card q-mb-sm"):
                                with ui.row().classes("justify-between w-full"):
                                    ui.label("Sighting Location:").classes("text-caption text-slate-400")
                                    ui.label(sub.location).classes("text-subtitle2 text-white")
                                with ui.row().classes("justify-between w-full"):
                                    ui.label("Sighting Date:").classes("text-caption text-slate-400")
                                    ui.label(sub.submitted_on.strftime('%Y-%m-%d %H:%M')).classes("text-subtitle2 text-white")
                                with ui.row().classes("justify-between w-full q-mt-sm border-t border-slate-700 q-pt-sm"):
                                    ui.label("AI Processing:").classes("text-caption text-slate-400")
                                    ui.badge("COMPLETED", color="green")
                                with ui.row().classes("justify-between w-full"):
                                    ui.label("Verification Status:").classes("text-caption text-slate-400")
                                    ui.badge(v_status, color="blue" if "Verification" in v_status else ("teal" if "Verified" in v_status else "red"))
                                if match_case:
                                    ui.label(match_case).classes("text-subtitle2 text-weight-bold text-center w-full text-blue-300 q-mt-md")
                                    
                    except Exception as e:
                        ui.notify(f"Search failed: {e}", type="negative")
                    finally:
                        db_session.remove()
                        
                ui.button("Search Status", on_click=search_tracking).classes("w-full").props("color=teal")

        # ── TAB 3: SEARCH REGISTERED CASES ─────────────────────────────────────
        with container_search:
            with ui.card().classes("glass-card w-full q-pa-lg"):
                ui.label("Public Missing Person Database").classes("text-h6 text-weight-bold text-white q-mb-xs")
                ui.label("Search the public database of active alerts. If you recognize anyone, file a sighting immediately.").classes("text-caption text-slate-400 q-mb-md")
                
                with ui.row().classes("w-full justify-between items-center q-mb-md q-col-gutter-sm"):
                    search_name = ui.input("Name").props("outlined dense").classes("col")
                    search_city = ui.input("City").props("outlined dense").classes("col")
                    ui.button(icon="search", on_click=lambda: run_db_search()).classes("glass-btn text-teal-400 q-py-sm")
                    
                cases_grid = ui.row().classes("w-full justify-center q-col-gutter-md q-pt-md")
                
                def run_db_search():
                    name = search_name.value
                    city = search_city.value
                    
                    db = db_session()
                    try:
                        # Fetch all Not Found cases
                        query = db.query(RegisteredCases).filter(RegisteredCases.status == "NF")
                        if name:
                            query = query.filter(RegisteredCases.name.like(f"%{name}%"))
                        if city:
                            query = query.filter(RegisteredCases.city.like(f"%{city}%"))
                            
                        results = query.all()
                        cases_grid.clear()
                        
                        if not results:
                            with cases_grid:
                                ui.label("No active alerts match your search parameters.").classes("text-subtitle1 text-slate-500 text-center w-full q-my-md")
                            return
                            
                        with cases_grid:
                            for c in results:
                                with ui.card().classes("col-12 col-sm-4 glass-card q-pa-md items-center text-center"):
                                    # Show original or age progressed image if available
                                    if c.original_image_path and os.path.exists(c.original_image_path):
                                        # Convert image to Base64 to serve locally
                                        with open(c.original_image_path, "rb") as image_file:
                                            b64 = base64.b64encode(image_file.read()).decode("utf-8")
                                        ui.image(f"data:image/jpeg;base64,{b64}").classes("w-32 h-32 rounded-full q-mb-sm object-cover")
                                    else:
                                        ui.icon("account_circle", size="5rem").classes("text-slate-600 q-mb-sm")
                                        
                                    ui.label(c.name).classes("text-h6 text-weight-bold text-white")
                                    ui.label(f"Age: {c.age} | City: {c.city}").classes("text-caption text-slate-400")
                                    ui.label(f"Last Seen: {c.last_seen}").classes("text-caption text-slate-300 q-mb-sm")
                                    
                                    # Sighting action
                                    def quick_report(case_city=c.city):
                                        show_tab("Report")
                                        sighting_loc.value = f"Seen near {case_city} "
                                        ui.notify(f"Reporting sighting for case from {case_city}", type="info")
                                        
                                    ui.button("File Sighting", on_click=lambda c_city=c.city: quick_report(c_city)).classes("w-full").props("color=teal size=sm")
                    except Exception as e:
                        ui.notify(f"Search failed: {e}", type="negative")
                    finally:
                        db_session.remove()
                        
                run_db_search()  # Run once initially

    # Success Dialog
    def success_dialog(sub_id: str):
        with ui.dialog() as dialog, ui.card().classes("glass-card q-pa-xl items-center text-center").style("max-width: 420px;"):
            ui.icon("check_circle", size="5rem").classes("text-teal-400 q-mb-md animate-bounce")
            ui.label("Report Submitted!").classes("text-h5 text-weight-bold text-white q-mb-xs")
            ui.label("Thank you for finding hope. Your report ID is:").classes("text-body2 text-slate-300")
            
            # Selectable ID badge
            with ui.card().classes("q-pa-sm q-my-md bg-slate-800 border border-slate-700 w-full"):
                ui.label(sub_id).classes("text-caption text-weight-bold text-teal-300 select-all")
                
            ui.label("Please SAVE this ID to track updates in the 'Track My Report' tab.").classes("text-caption text-red-400 q-mb-lg")
            ui.button("Done", on_click=lambda: dialog.close()).classes("w-full").props("color=teal")
        dialog.open()
