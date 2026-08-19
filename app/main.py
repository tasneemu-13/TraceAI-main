import os

from fastapi import FastAPI
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
from app.frontend import (
    landing,
    login,
    public,
    officer,
    admin,
    case_details,
    mobile,
    contact,
    company,
    faq,
    helpdesk,
    forums,
)


# ============================================================
# 1. INITIALIZE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# 2. SEED DEFAULT ACCOUNTS
# ============================================================

def seed_database():
    db = SessionLocal()

    try:
        # Check if users table is empty
        if db.query(User).count() == 0:
            print("[Database Seed] Seeding default admin and officer accounts...")

            # Admin account
            gagan_admin = User(
                username="Tasneem",
                email="dewastasneem618@gmail.com",
                hashed_password="$2b$12$QpCq.lHWfb6yTWr98fTuZubW8lc/KADvujYMEmvHTPuUZbwRDIknW",
                role="Admin",
                name="Tasneem Dewaswala",
                city="Mumbai",
                area="Bandra West",
                is_verified=True,
            )

            # Default Officer
            officer_user = User(
                username="officer",
                email="officer@traceai.gov.in",
                hashed_password=os.getenv(
                    "OFFICER_PASSWORD_HASH",
                    "$2b$12$ByZbwxrcVXLQO4zjI95OteXToaBiwWDqujsHiKfeGzionz0VqAG",
                ),
                role="Officer",
                name="Officer Amit Kumar",
                city="Delhi",
                area="Sector 1",
                is_verified=True,
            )

            db.add(gagan_admin)
            db.add(officer_user)
            db.commit()

            print("[Database Seed] Seed completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[Database Seed Error] Failed: {e}")

    finally:
        db.close()


seed_database()


# ============================================================
# 3. CREATE FASTAPI APPLICATION
# ============================================================

fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.TAGLINE,
    version="1.0.0",
)


# ============================================================
# 4. STATIC FILES
# ============================================================

nicegui_app.add_static_files(
    "/static",
    "app/static",
)


# ============================================================
# 5. INCLUDE REST API ROUTERS
# ============================================================

fastapi_app.include_router(auth_router.router)
fastapi_app.include_router(case_router.router)
fastapi_app.include_router(sub_router.router)
fastapi_app.include_router(map_router.router)


# ============================================================
# 6. NICEGUI PAGES
# ============================================================

@ui.page("/")
def index():
    landing.content()


@ui.page("/login")
def login_page():
    login.content()


@ui.page("/public")
def public_page():
    public.content()


@ui.page("/officer")
def officer_page():
    officer.content()


@ui.page("/admin")
def admin_page():
    admin.content()


@ui.page("/cases/{case_id}")
def case_details_page(case_id: str):
    case_details.content(case_id)


@ui.page("/mobile")
def mobile_page():
    mobile.content()


@ui.page("/contact")
def contact_page():
    contact.content()


@ui.page("/company")
def company_page():
    company.content()


@ui.page("/faq")
def faq_page():
    faq.content()


@ui.page("/helpdesk")
def helpdesk_page():
    helpdesk.content()


@ui.page("/forums")
def forums_page():
    forums.content()


# ============================================================
# 7. CONNECT NICEGUI TO FASTAPI
# ============================================================

nicegui_storage_secret = os.getenv(
    "NICEGUI_STORAGE_SECRET",
    "local-development-secret-change-in-render",
)

ui.run_with(
    fastapi_app,
    storage_secret=nicegui_storage_secret,
)


# ============================================================
# 8. START SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    print(f"[TraceAI] Starting server on 0.0.0.0:{port}")

    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
    )