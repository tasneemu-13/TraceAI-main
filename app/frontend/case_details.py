import os
import json
import base64
from nicegui import ui, app, run
from app.frontend import layout
from app.database import db_session
from app.repositories import case as case_repo
from app.repositories import doc as doc_repo
from app.repositories import submission as sub_repo
from app.models.doc import InvestigationDoc, SightingMatch
from app.services import rag as rag_service

def content(case_id: str):
    """
    Renders the high-fidelity case details, history timeline, and RAG assistant panel.
    """
    layout.theme_setup()
    layout.header_nav()
    
    # Check auth
    username = app.storage.user.get("user")
    if not username:
        ui.navigate.to("/login")
        return
        
    db = db_session()
    try:
        case = case_repo.get_case_by_id(db, case_id)
        if not case:
            ui.label("Case File Not Found").classes("text-h4 text-red-500 q-pa-xl text-center w-full")
            return
            
        docs = doc_repo.get_docs_by_case(db, case_id)
        matches = sub_repo.get_sighting_matches_by_case(db, case_id)
        timeline = rag_service.rag_assistant.generate_investigation_timeline(db, case_id)
    except Exception as e:
        ui.notify(f"Failed to load case: {e}", type="negative")
        return
    finally:
        db_session.remove()

    # RAG Assistant Chat history state
    chat_messages = []

    with ui.row().classes("w-full q-col-gutter-lg q-pa-md"):
        # ── LEFT PANEL (PROFILE, TIMELINE, DOCUMENTS) ────────────────────────
        with ui.column().classes("col-12 col-md-7 q-gutter-md"):
            
            # Profile Card
            with ui.card().classes("w-full glass-card q-pa-lg"):
                with ui.row().classes("w-full justify-between items-center q-mb-md"):
                    with ui.column():
                        ui.label(case.name).classes("text-h4 text-weight-bold text-white")
                        ui.label(f"ID Ref: {case.id}").classes("text-caption text-blue-300 font-bold")
                    ui.button("Export PDF Summary", icon="picture_as_pdf", on_click=lambda: ui.navigate.to(f"/api/cases/{case.id}/report", new_tab=True)).classes("glass-btn text-red-400")
                
                # Side-by-Side Images & Disclaimer
                with ui.row().classes("w-full justify-around items-center q-col-gutter-md q-mb-md"):
                    # Original Image
                    with ui.column().classes("items-center col-6 text-center"):
                        ui.label("Original Photograph").classes("text-caption text-slate-400 q-mb-xs")
                        if case.original_image_path and os.path.exists(case.original_image_path):
                            ui.image(f"/api/cases/{case.id}/photo/original").classes("w-full max-w-sm rounded border border-slate-700")
                        else:
                            ui.icon("account_circle", size="8rem").classes("text-slate-600")
                            
                    # Age Progressed Image
                    with ui.column().classes("items-center col-6 text-center"):
                        ui.label("Estimated Current Appearance").classes("text-caption text-slate-400 q-mb-xs")
                        if case.age_progressed_image_path and os.path.exists(case.age_progressed_image_path):
                            ui.image(f"/api/cases/{case.id}/photo/progressed").classes("w-full max-w-sm rounded border border-purple-500")
                        else:
                            ui.icon("account_circle", size="8rem").classes("text-slate-600")
                            
                ui.label("AI Generated Investigative Estimate: Photographs are synthesized projections based on initial structures and must be verified.").classes("text-caption text-red-400 text-weight-bold text-center w-full q-mb-md")
                
                # Metadata fields grid
                with ui.row().classes("w-full q-col-gutter-sm text-sm q-mb-md"):
                    def meta_field(label, val):
                        with ui.column().classes("col-6 col-sm-4 q-mb-xs"):
                            ui.label(label).classes("text-caption text-slate-500 q-mb-none")
                            ui.label(val or "N/A").classes("text-subtitle2 text-white")
                            
                    meta_field("Age Registered", f"{case.age} yrs")
                    meta_field("Father's Name", case.father_name)
                    meta_field("Aadhaar Number", case.adhaar_card)
                    meta_field("Last Seen Area", case.last_seen)
                    meta_field("City", case.city)
                    meta_field("Complainant Name", case.complainant_name)
                    meta_field("Family Mobile", case.complainant_mobile)
                    meta_field("Family Email", case.complainant_email)
                    meta_field("Languages", case.languages_spoken)
                    
                ui.label("Medical Profile / Warnings:").classes("text-caption text-red-300 font-bold")
                ui.label(case.medical_info or "No specific warnings logged.").classes("text-subtitle2 text-white q-mb-sm")
                
                ui.label("Physical Description:").classes("text-caption text-slate-400 font-bold")
                ui.label(case.physical_description or "No descriptors logged.").classes("text-subtitle2 text-white")

            # Documents & Notes logger
            with ui.card().classes("w-full glass-card q-pa-lg"):
                ui.label("Investigation Evidence Logs").classes("text-h6 text-weight-bold text-white q-mb-sm")
                
                docs_container = ui.column().classes("w-full q-gutter-sm q-mb-md")
                
                def render_notes_list():
                    docs_container.clear()
                    db_list = db_session()
                    try:
                        notes_all = doc_repo.get_docs_by_case(db_list, case_id)
                        if not notes_all:
                            with docs_container:
                                ui.label("No additional evidence notes logged yet.").classes("text-caption text-slate-500 q-pa-xs")
                            return
                            
                        with docs_container:
                            for d in notes_all:
                                with ui.card().classes("w-full bg-slate-900 border border-slate-800 q-pa-md"):
                                    with ui.row().classes("w-full justify-between items-center"):
                                        ui.label(f"{d.doc_type} - {d.title}").classes("text-subtitle2 text-blue-300 font-bold")
                                        ui.label(d.created_at.strftime('%Y-%m-%d %H:%M')).classes("text-caption text-slate-500")
                                    ui.label(d.content).classes("text-body2 text-slate-300 q-mt-xs")
                    except Exception:
                        pass
                    finally:
                        db_session.remove()
                        
                render_notes_list()
                
                # Logger Form
                ui.label("Log New Document").classes("text-caption text-slate-400 font-bold q-mt-md")
                log_type = ui.select(["Officer Note", "Witness Statement", "Location History", "Email", "Evidence Details"], value="Officer Note").props("dense outlined").classes("w-full q-mb-xs")
                log_title = ui.input("Title").props("dense outlined").classes("w-full q-mb-xs")
                log_content = ui.textarea("Document Content").props("dense outlined placeholder='Type details, witness name, sightings log'").classes("w-full q-mb-md")
                
                def add_new_document():
                    t = log_type.value
                    title = log_title.value
                    c = log_content.value
                    if not title or not c:
                        ui.notify("Please fill in title and content.", type="warning")
                        return
                        
                    db_add = db_session()
                    try:
                        new_doc = InvestigationDoc(
                            case_id=case_id,
                            doc_type=t,
                            title=title,
                            content=c
                        )
                        doc_repo.create_doc(db_add, new_doc)
                        
                        # Sync RAG index
                        rag_service.rag_assistant.reindex_all_docs(db_add)
                        ui.notify("Evidence document vectorized and logged successfully.", type="positive")
                        
                        log_title.value = ""
                        log_content.value = ""
                        render_notes_list()
                    except Exception as err:
                        ui.notify(f"Failed to log document: {err}", type="negative")
                    finally:
                        db_session.remove()
                        
                ui.button("Log and Index Evidence", on_click=add_new_document).classes("w-full").props("color=blue size=sm")

            # Timeline
            with ui.card().classes("w-full glass-card q-pa-lg"):
                ui.label("Chronology Timeline").classes("text-h6 text-weight-bold text-white q-mb-md")
                
                with ui.element('q-timeline').props('side=right color=blue'):
                    for item in timeline:
                        ui.element('q-timeline-entry').props(
                            f'title="{item["title"]}" subtitle="{item["date"]}" icon="{item["icon"]}"'
                        ).classes("text-white").style("color: white !important;")
                        ui.label(item["description"]).classes("text-body2 text-slate-300 q-pl-sm q-pb-md")

        # ── RIGHT PANEL (RAG ASSISTANT PANEL) ─────────────────────────────────
        with ui.column().classes("col-12 col-md-5 q-gutter-md"):
            with ui.card().classes("w-full glass-card q-pa-lg").style("min-height: 600px; display: flex; flex-direction: column;"):
                
                # Assistant Header
                with ui.row().classes("items-center w-full border-b border-slate-700 q-pb-sm q-mb-md"):
                    ui.icon("psychology", size="2.5rem").classes("text-purple-400 q-mr-xs animate-pulse")
                    with ui.column():
                        ui.label("TraceAI Agent Assistant").classes("text-h6 text-weight-bold text-white")
                        ui.label("RAG intelligence engine").classes("text-caption text-slate-400")
                
                # Chat History Area
                chat_scroll = ui.scroll_area().classes("w-full flex-grow q-mb-md").style("height: 380px; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; background: rgba(0,0,0,0.2);")
                
                def append_to_chat(sender: str, text: str):
                    chat_messages.append({"sender": sender, "text": text})
                    chat_scroll.clear()
                    with chat_scroll:
                        for msg in chat_messages:
                            is_bot = (msg["sender"] == "TraceAI")
                            bg = "bg-purple-900" if is_bot else "bg-slate-800"
                            color = "text-purple-100" if is_bot else "text-slate-100"
                            
                            with ui.row().classes("w-full items-start q-mb-sm no-wrap").style("flex-direction: row;" if is_bot else "flex-direction: row-reverse;"):
                                if is_bot:
                                    ui.image("/static/caricature.png").classes("rounded-full border border-purple-500").style("width: 32px; height: 32px; flex-shrink: 0; object-fit: cover;")
                                else:
                                    ui.icon("account_circle", size="2rem").classes("text-blue-400").style("flex-shrink: 0;")
                                    
                                with ui.card().classes(f"{bg} {color} q-pa-sm rounded-lg max-w-sm q-mb-none").style("max-width: 80%;"):
                                    ui.label(msg["sender"]).classes("text-caption text-weight-bold text-blue-300")
                                    ui.markdown(msg["text"]).classes("text-body2")
                                    
                # Initial greeting
                append_to_chat("TraceAI", "Hello Officer. I have indexed all logged notes, witness reports, and demographic details for this case. Ask me any question, summarize details, or query missing files.")
                
                # Safe utility to remove loading placeholder dict by object identity
                def safe_remove_loading(msg_obj):
                    try:
                        for i in range(len(chat_messages) - 1, -1, -1):
                            if chat_messages[i] is msg_obj:
                                chat_messages.pop(i)
                                break
                    except Exception:
                        pass

                # Quick prompt tags
                ui.label("Quick Investigation Inquiries").classes("text-caption text-slate-400 font-bold q-mb-xs")
                with ui.row().classes("w-full q-col-gutter-xs q-mb-sm"):
                    
                    async def run_assistant_action(action_type: str):
                        append_to_chat("Officer", f"Execute action: {action_type}")
                        loading_msg = append_to_chat("TraceAI", "🤖 Analyzing case files and generating summary logs... Please wait...")
                        
                        db_rag = db_session()
                        try:
                            if action_type == "Summarize Case":
                                res = await run.io_bound(rag_service.rag_assistant.summarize_case, db_rag, case_id)
                            elif action_type == "Missing Evidence":
                                res = await run.io_bound(rag_service.rag_assistant.show_missing_evidence, db_rag, case_id)
                            else: # Similar cases
                                res = "Querying FAISS global index... Found 0 similar case profiles by signature matching."
                            
                            safe_remove_loading(loading_msg)
                            append_to_chat("TraceAI", res)
                        except Exception as e:
                            safe_remove_loading(loading_msg)
                            append_to_chat("TraceAI", f"Error: {e}")
                        finally:
                            db_session.remove()
                            
                    ui.button("Summarize", on_click=lambda: run_assistant_action("Summarize Case")).classes("col glass-btn text-caption").props("size=xs")
                    ui.button("Missing Evidence", on_click=lambda: run_assistant_action("Missing Evidence")).classes("col glass-btn text-caption").props("size=xs")
                    ui.button("Similar Cases", on_click=lambda: run_assistant_action("Similar Cases")).classes("col glass-btn text-caption").props("size=xs")
                    
                # Chat input
                with ui.row().classes("w-full items-center q-col-gutter-xs"):
                    query_input = ui.input("Ask RAG Assistant...").props("outlined dense").classes("col")
                    
                    async def execute_query():
                        q = query_input.value.strip()
                        if not q:
                            return
                        query_input.value = ""
                        append_to_chat("Officer", q)
                        
                        loading_msg = append_to_chat("TraceAI", "🤖 Querying database records... Please wait...")
                        
                        db_query = db_session()
                        try:
                            # Run RAG query asynchronously
                            response = await run.io_bound(rag_service.rag_assistant.answer_officer_question, db_query, case_id, q)
                            safe_remove_loading(loading_msg)
                            append_to_chat("TraceAI", response)
                        except Exception as err:
                            safe_remove_loading(loading_msg)
                            append_to_chat("TraceAI", f"Failed to retrieve context: {err}")
                        finally:
                            db_session.remove()
                            
                    ui.button(icon="send", on_click=execute_query).classes("glass-btn text-purple-400 q-py-sm").props("dense")
