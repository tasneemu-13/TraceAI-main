import os
import json
import base64
from datetime import datetime
from uuid import uuid4
from nicegui import ui, app
from app.frontend import layout
from app.database import db_session
from app.models.submission import PublicSubmissions
from app.repositories import submission as sub_repo
from app.services import matching as match_service
from app.config import settings

def content():
    """
    Renders the citizen mobile WebView client app.
    """
    layout.theme_setup()
    
    # Custom CSS style to override defaults and make it look like a native smartphone screen
    ui.add_head_html('''
    <style>
        .mobile-shell {
            max-width: 440px !important;
            width: 95vw !important;
            margin: 0 auto !important;
            background: rgba(15, 23, 42, 0.75) !important;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(16px);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 40px rgba(20, 184, 166, 0.05);
            padding: 24px;
            overflow-y: auto;
        }
        @media (max-width: 480px) {
            .mobile-shell {
                max-width: 100% !important;
                width: 100% !important;
                min-height: 100vh !important;
                border-radius: 0px !important;
                border: none !important;
                box-shadow: none !important;
                margin: 0 !important;
                padding: 16px !important;
            }
        }
        .compact-uploader .q-uploader__list {
            display: none !important;
        }
        .compact-uploader .q-uploader__header {
            background: transparent !important;
        }
        .compact-uploader {
            background: rgba(15, 23, 42, 0.4) !important;
            border: 1px dashed rgba(20, 184, 166, 0.4) !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }
    </style>
    ''')
    
    with ui.column().classes("w-full items-center justify-center q-py-lg").style("min-height: 100vh; background: #030712;"):
        # Mobile Phone Container Shell
        with ui.column().classes("mobile-shell items-stretch q-gutter-md"):
            
            # App Header nav
            with ui.row().classes("justify-between items-center border-b border-slate-800/80 q-pb-sm"):
                with ui.row().classes("items-center"):
                    ui.icon("radar", size="1.8rem").classes("text-teal-400")
                    ui.label("TraceAI Citizen").classes("text-subtitle1 text-weight-bold text-white q-ml-xs")
                ui.button(icon="sync", on_click=lambda: ui.notify("Syncing database alerts...", type="info")).classes("glass-btn text-teal-400").props("dense size=sm")

            # Notification Banner
            with ui.card().classes("q-pa-sm glass-card border border-teal-500/20").style("background: rgba(20, 184, 166, 0.05);"):
                with ui.row().classes("items-center q-gutter-xs"):
                    ui.icon("notifications_active", size="1.2rem").classes("text-teal-400 animate-pulse")
                    ui.label("Sighting Alert: Noida Sector 128 active search").classes("text-caption text-teal-200")

            # Form Input section
            with ui.column().classes("q-gutter-sm items-stretch"):
                ui.label("Submit Quick Sighting Report").classes("text-subtitle2 text-weight-bold text-teal-300 q-mb-xs")
                
                # Anonymous Switch
                anonymous_switch = ui.switch("Submit Anonymously", value=False).props("color=teal dark").classes("text-slate-300 text-xs q-mb-xs")
                
                # Form Inputs
                with ui.input("Name", placeholder="Enter your full name").props("outlined color=teal dark label-color=teal").classes("w-full") as sub_name:
                    with sub_name.add_slot("prepend"):
                        ui.icon("person").classes("text-teal-400")
                
                # Change handler for anonymous switch
                def on_anon_change(e):
                    if e.value:
                        sub_name.value = ""
                        sub_name.visible = False
                    else:
                        sub_name.visible = True
                anonymous_switch.on_value_change(on_anon_change)

                with ui.input("Mobile *", placeholder="Enter contact number").props("outlined color=teal dark label-color=teal mask=##########").classes("w-full") as sub_mobile:
                    with sub_mobile.add_slot("prepend"):
                        ui.icon("phone").classes("text-teal-400")

                with ui.input("Location Seen *", placeholder="Where did you spot them?").props("outlined color=teal dark label-color=teal").classes("w-full") as sub_loc:
                    with sub_loc.add_slot("prepend"):
                        ui.icon("place").classes("text-teal-400")
                        
                with ui.textarea("Details / Description", placeholder="Add any details (clothing, physical markers, direction...)").props("outlined color=teal dark label-color=teal autogrow").classes("w-full") as sub_desc:
                    with sub_desc.add_slot("prepend"):
                        ui.icon("description").classes("text-teal-400")
            
            # GPS Location Tracker Card
            lat_store = ui.number().style("display:none;")
            lon_store = ui.number().style("display:none;")
            
            with ui.card().classes("bg-slate-900/85 border border-slate-800/80 rounded-xl q-pa-sm row items-center justify-between").style("display:flex; flex-direction:row;"):
                with ui.row().classes("items-center"):
                    gps_icon = ui.icon("location_off", size="1.5rem").classes("text-slate-500")
                    with ui.column().classes("q-ml-sm"):
                        ui.label("Device GPS Location").classes("text-caption text-slate-400 font-bold")
                        gps_coords = ui.label("GPS Coordinates: Not Set").classes("text-caption text-slate-500")
                
                async def fetch_mobile_gps():
                    gps_coords.text = "Tracking location..."
                    gps_icon.name = "my_location"
                    gps_icon.classes("text-orange-400 animate-pulse", remove="text-slate-500 text-teal-400")
                    
                    coords = await ui.run_javascript('''
                        new Promise((resolve) => {
                            navigator.geolocation.getCurrentPosition(
                                (p) => resolve({lat: p.coords.latitude, lon: p.coords.longitude}),
                                (e) => resolve(null),
                                {timeout: 5000, enableHighAccuracy: true}
                            );
                        });
                    ''')
                    if coords:
                        lat_store.value = coords["lat"]
                        lon_store.value = coords["lon"]
                        gps_coords.text = f"{coords['lat']:.5f}, {coords['lon']:.5f}"
                        gps_icon.name = "location_on"
                        gps_icon.classes("text-teal-400", remove="text-orange-400 animate-pulse")
                        ui.notify("GPS Coordinates locked!", type="positive")
                    else:
                        gps_coords.text = "GPS access denied or timed out"
                        gps_icon.name = "location_off"
                        gps_icon.classes("text-red-400", remove="text-orange-400 animate-pulse text-teal-400")
                        ui.notify("Check location permissions on your phone.", type="warning")
                        
                gps_btn = ui.button(icon="gps_fixed", on_click=fetch_mobile_gps).classes("glass-btn text-teal-400").props("dense round")
                
            # Camera Viewport Card / Attachment Preview
            with ui.card().classes("bg-slate-900 border-2 border-dashed border-teal-800/40 rounded-xl q-pa-md text-center justify-center items-center").style("background: rgba(15, 23, 42, 0.6); position: relative;") as preview_card:
                placeholder_col = ui.column().classes("items-center justify-center w-full")
                with placeholder_col:
                    ui.icon("photo_camera", size="3rem").classes("text-teal-500 q-mb-sm")
                    ui.label("Face Photo Required").classes("text-subtitle2 text-teal-300 font-bold")
                    ui.label("Snap or choose photo using uploader below").classes("text-caption text-slate-500")
                
                image_preview = ui.image().classes("w-full rounded-lg").style("max-height: 220px; object-fit: cover;")
                image_preview.visible = False
                
                # Close button to remove current photo
                def remove_photo():
                    staged_file["content"] = None
                    image_preview.source = ""
                    image_preview.visible = False
                    placeholder_col.visible = True
                    upload_badge.text = "No photo attached"
                    upload_badge.classes("text-slate-500", remove="text-teal-400")
                    ui.notify("Photo removed", type="info")
                    
                remove_btn = ui.button(icon="close", on_click=remove_photo).classes("absolute top-2 right-2 bg-red-800/80 text-white").props("dense round size=sm")
                remove_btn.bind_visibility_from(image_preview, "visible")
            
            staged_file = {"content": None, "name": "photo.jpg"}
            
            async def handle_mobile_upload(e):
                staged_file["content"] = await e.file.read()
                staged_file["name"] = e.file.name
                base_data = base64.b64encode(staged_file["content"]).decode('utf-8')
                image_preview.source = f"data:image/jpeg;base64,{base_data}"
                image_preview.visible = True
                placeholder_col.visible = False
                upload_badge.text = "✓ Face Photo Attached"
                upload_badge.classes("text-teal-400", remove="text-slate-500")
                ui.notify("Photo successfully attached", type="positive")

            ui.upload(on_upload=handle_mobile_upload, label="Snap Camera / Attach Photo", auto_upload=True).props("flat bordered dark color=teal accept=image/* capture=camera").classes("w-full compact-uploader")
            upload_badge = ui.label("No photo attached").classes("text-caption text-slate-500 q-mb-sm")
            
            # Offline Drafts checklist
            drafts_list_col = ui.column().classes("w-full q-gutter-xs q-mt-sm")
            
            def save_offline_draft():
                m = sub_mobile.value
                l = sub_loc.value
                n = sub_name.value
                if not m or not l:
                    ui.notify("Mobile and Location are required to save draft.", type="warning")
                    return
                # Save draft using JS
                ui.run_javascript(f'''
                    let drafts = JSON.parse(localStorage.getItem('traceai_drafts') || '[]');
                    drafts.push({{
                        name: "{n}",
                        mobile: "{m}",
                        location: "{l}",
                        timestamp: new Date().toLocaleString()
                    }});
                    localStorage.setItem('traceai_drafts', JSON.stringify(drafts));
                ''')
                ui.notify("Sighting saved as offline draft", type="positive")
                load_drafts_ui()
                
            async def load_drafts_ui():
                drafts_list_col.clear()
                drafts_json = await ui.run_javascript('''
                    localStorage.getItem('traceai_drafts') || '[]'
                ''')
                drafts = json.loads(drafts_json)
                if not drafts:
                    with drafts_list_col:
                        ui.label("No offline drafts saved.").classes("text-caption text-slate-500 q-pa-xs w-full text-center")
                    return
                    
                with drafts_list_col:
                    ui.label("Offline Drafts Checklist:").classes("text-caption text-slate-400 font-bold")
                    for i, d in enumerate(drafts):
                        with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-sm row items-center justify-between").style("display:flex; flex-direction:row;"):
                            with ui.column():
                                ui.label(d["location"]).classes("text-caption text-white font-bold")
                                ui.label(f"Saved: {d['timestamp']}").classes("text-caption text-slate-500").style("font-size:10px;")
                            
                            def fill_from_draft(dr=d, idx=i):
                                sub_name.value = dr["name"]
                                sub_mobile.value = dr["mobile"]
                                sub_loc.value = dr["location"]
                                ui.run_javascript(f'''
                                    let drafts = JSON.parse(localStorage.getItem('traceai_drafts') || '[]');
                                    drafts.splice({idx}, 1);
                                    localStorage.setItem('traceai_drafts', JSON.stringify(drafts));
                                ''')
                                ui.notify("Draft loaded into active form.", type="info")
                                load_drafts_ui()
                            ui.button(icon="edit", on_click=lambda dr=d, idx=i: fill_from_draft(dr, idx)).classes("glass-btn text-teal-300").props("dense size=xs")

            # Action controls
            with ui.row().classes("w-full q-col-gutter-sm"):
                ui.button("Save Draft", icon="save", on_click=save_offline_draft).classes("col glass-btn text-slate-300").style("height: 48px;")
                
                async def submit_live_report():
                    m = sub_mobile.value
                    l = sub_loc.value
                    if not m or not l:
                        ui.notify("Mobile and Location are required.", type="warning")
                        return
                    if not staged_file["content"]:
                        ui.notify("Please capture a photo first.", type="warning")
                        return
                        
                    db = db_session()
                    try:
                        sub_id = str(uuid4())
                        dest_path = os.path.join(settings.UPLOAD_DIR, f"{sub_id}.jpg")
                        with open(dest_path, "wb") as f:
                            f.write(staged_file["content"])
                            
                        # Face encodings landmarks verification
                        import cv2
                        img = cv2.imread(dest_path)
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        landmarks = match_service.extract_face_mesh_from_frame(img_rgb)
                        
                        if not landmarks:
                            if os.path.exists(dest_path):
                                os.remove(dest_path)
                            ui.notify("No face detected in photo. Please ensure face is clearly visible.", type="negative")
                            return
                            
                        new_sub = PublicSubmissions(
                            id=sub_id,
                            submitted_by=None if anonymous_switch.value else (sub_name.value or "Anonymous Mobile Citizen"),
                            face_mesh=json.dumps(landmarks),
                            location=l,
                            mobile=m,
                            status="NF",
                            image_path=dest_path,
                            is_anonymous=anonymous_switch.value or (not bool(sub_name.value)),
                            latitude=lat_store.value,
                            longitude=lon_store.value,
                            description=sub_desc.value or "Mobile reporting sighting",
                            sighting_time=datetime.utcnow()
                        )
                        sub_repo.create_submission(db, new_sub)
                        match_service.run_face_matching(db)
                        
                        ui.notify("Sighting report uploaded successfully!", type="positive")
                        
                        # Reset form
                        sub_name.value = ""
                        sub_mobile.value = ""
                        sub_loc.value = ""
                        sub_desc.value = ""
                        remove_photo()
                        
                    except Exception as e:
                        ui.notify(f"Submit error: {e}", type="negative")
                    finally:
                        db_session.remove()
                        
                ui.button("Upload Sighting", icon="cloud_upload", on_click=submit_live_report).classes("col").props("color=teal").style("height: 48px;")

            def clear_form():
                sub_name.value = ""
                sub_mobile.value = ""
                sub_loc.value = ""
                sub_desc.value = ""
                remove_photo()
                ui.notify("Form cleared", type="info")

            ui.button("Clear Form", icon="clear_all", on_click=clear_form).classes("w-full glass-btn text-xs text-slate-400").props("dense")
            
            # Render drafts checklist initially
            ui.timer(0.5, load_drafts_ui, once=True)
            
            # Back to Web portal button
            ui.button("Back to Web Portal", on_click=lambda: ui.navigate.to("/")).classes("w-full glass-btn text-xs q-mt-md text-slate-400")
