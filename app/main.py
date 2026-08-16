import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from nicegui import ui, app as nicegui_app

# Core imports
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.user import User

# Router imports
from app.routes import auth as auth_router
from app.routes import case as case_router
from app.routes import submission as sub_router
from app.routes import map as map_router

# Frontend page imports
from app.frontend import landing, login, public, officer, admin, case_details, mobile, contact, company, faq, helpdesk, forums

# 1. Initialize Database Tables
Base.metadata.create_all(bind=engine)

# 2. Seed Default Accounts
def seed_database():
    db = SessionLocal()
    try:
        # Check if users table is empty
        if db.query(User).count() == 0:
            print("[Database Seed] Seeding default admin and officer accounts...")
            
            # Tasneem (Admin)
            gagan_admin = User(
                username="Tasneem",
                email="dewastasneem618@gmail.com",
                hashed_password="$2b$12$QpCq.lHWfb6yTWr98fTuZubW8lc/KADvujYMEmvHTPuUZbwRDIknW", # Password is "abc"
                role="Admin",
                name="Tasneem Dewaswala",
                city="Mumbai",
                area="Bandra West",
                is_verified=True
            )
            
            # Default Officer
            officer_user = User(
                username="officer",
                email="officer@traceai.gov.in",
                hashed_password=os.getenv("OFFICER_PASSWORD_HASH", "$2b$12$ByZbwxrcvCXVLQO4zjI95OteXToaBiwWDqujsHiKfeGzionz0VqAG"), # Default to "abc"
                role="Officer",
                name="Officer Amit Kumar",
                city="Delhi",
                area="Sector 1",
                is_verified=True
            )
            
            db.add(gagan_admin)
            db.add(officer_user)
            db.commit()
            print("[Database Seed] Seed completed successfully.")
    except Exception as e:
        print(f"[Database Seed Error] Failed: {e}")
    finally:
        db.close()

seed_database()

# 3. Create FastAPI Application
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.TAGLINE,
    version="1.0.0"
)

# Serve static uploads and Leaflet library files via NiceGUI
nicegui_app.add_static_files("/static", "app/static")

# Include REST API Routers
fastapi_app.include_router(auth_router.router)
fastapi_app.include_router(case_router.router)
fastapi_app.include_router(sub_router.router)
fastapi_app.include_router(map_router.router)

# 4. Mount NiceGUI Pages
@ui.page('/')
def index():
    landing.content()

@ui.page('/login')
def login_page():
    login.content()

@ui.page('/public')
def public_page():
    public.content()

@ui.page('/officer')
def officer_page():
    officer.content()

@ui.page('/admin')
def admin_page():
    admin.content()

@ui.page('/cases/{case_id}')
def case_details_page(case_id: str):
    case_details.content(case_id)

@ui.page('/mobile')
def mobile_page():
    mobile.content()

@ui.page('/contact')
def contact_page():
    contact.content()

@ui.page('/company')
def company_page():
    company.content()

@ui.page('/faq')
def faq_page():
    faq.content()

@ui.page('/helpdesk')
def helpdesk_page():
    helpdesk.content()

@ui.page('/forums')
def forums_page():
    forums.content()

# Initialize NiceGUI with FastAPI mounting
ui.run_with(
    fastapi_app,
    storage_secret="traceai_super_secret_session_key_12389127391823"
)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Dynamically grab Render's PORT (defaults to 8080 locally)
    port = int(os.environ.get("PORT", 8080))
    
    # Run uvicorn directly on the app instance instead of string reloading
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)


'''if __name__ == "__main__":
    import uvicorn
    # Startup uvicorn server serving the FastAPI + NiceGUI application
    uvicorn.run("app.main:fastapi_app", host="0.0.0.0", port=8080, reload=True)'''
