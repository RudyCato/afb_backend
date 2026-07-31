import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import get_current_staff_optional
from .database import Base, engine
from .routers import customers, products, inventory, orders, packing, shipping, reports, production, pallets, packaging, order_tasks, mixes, applications, sops, admin, returns, receipts, report_pdfs, scan, employee_applications, jobs, review
from .routers import auth as auth_router

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Security config, driven by environment so nothing has to change in code
# between local dev and Render production.
# ---------------------------------------------------------------------------
# ALLOWED_ORIGINS: comma-separated list of origins allowed to call this API
# from a browser (CORS). Set this to your real domain(s) in Render, e.g.
#   ALLOWED_ORIGINS=https://afb-backend-58ys.onrender.com,https://americanfoodbeverage.com
# Falls back to localhost + the known Render URL so local dev and the
# current deployment keep working if it's not set yet.
_default_origins = "http://localhost:8000,http://127.0.0.1:8000,https://afb-backend-58ys.onrender.com"
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]

# COOKIE_SECURE: whether the session cookie requires HTTPS. Defaults to
# "on" whenever we're talking to a real Postgres database (i.e. production),
# and "off" for local SQLite dev so testing over plain http still works.
_is_local_sqlite = os.environ.get("DATABASE_URL", "sqlite:///./afb.db").startswith("sqlite")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false" if _is_local_sqlite else "true").lower() == "true"

app = FastAPI(
    title="American Food & Beverage — Operations API",
    description="Backend for inventory, packing, customers, shipping/delivery tracking and reporting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signed-cookie sessions for staff login. Set SESSION_SECRET in production
# (e.g. Render env var) - falls back to a dev-only value locally so nothing
# breaks if it's not configured yet.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-only-change-me-in-render-env-vars"),
    session_cookie="afb_staff_session",
    max_age=60 * 60 * 12,  # 12 hours
    same_site="lax",
    https_only=COOKIE_SECURE,
)

app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(packing.router)
app.include_router(shipping.router)
app.include_router(reports.router)
app.include_router(production.router)
app.include_router(pallets.router)
app.include_router(packaging.router)
app.include_router(order_tasks.router)
app.include_router(mixes.router)
app.include_router(applications.router)
app.include_router(sops.router)
app.include_router(returns.router)
app.include_router(receipts.router)
app.include_router(report_pdfs.router)
app.include_router(scan.router)
app.include_router(employee_applications.router)
app.include_router(jobs.router)
app.include_router(review.router)

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")

app.mount("/icons", StaticFiles(directory=os.path.join(WEB_DIR, "icons")), name="icons")

# Screenshots attached to review-portal workflow pages (see app/routers/review.py).
# The directory is created by that router's own import-time setup, but guard
# here too in case main.py's import order ever changes.
os.makedirs(os.path.join(WEB_DIR, "review-media"), exist_ok=True)
app.mount("/review-media", StaticFiles(directory=os.path.join(WEB_DIR, "review-media")), name="review-media")


@app.get("/manifest.json")
def manifest():
    return FileResponse(os.path.join(WEB_DIR, "manifest.json"), media_type="application/manifest+json")


@app.get("/order", response_class=FileResponse)
def order_page():
    return FileResponse(os.path.join(WEB_DIR, "order.html"))


def _staff_gate(next_path: str, staff):
    """Shared redirect-to-login logic for staff-only pages."""
    if staff is None:
        return RedirectResponse(url=f"/login?next={next_path}")
    return None


@app.get("/dashboard")
def dashboard_page(staff=Depends(get_current_staff_optional)):
    gate = _staff_gate("/dashboard", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "dashboard.html"))


@app.get("/production")
def production_page(staff=Depends(get_current_staff_optional)):
    gate = _staff_gate("/production", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "production.html"))


@app.get("/stock")
def stock_page(staff=Depends(get_current_staff_optional)):
    """Dedicated inventory/stock-count page — separate path from the
    /inventory API router (list/adjust/location/transactions) mounted
    below, so the two don't collide."""
    gate = _staff_gate("/stock", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "inventory.html"))


@app.get("/login", response_class=FileResponse)
def login_page():
    return FileResponse(os.path.join(WEB_DIR, "login.html"))


@app.get("/change-password")
def change_password_page(staff=Depends(get_current_staff_optional)):
    gate = _staff_gate("/change-password", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "change-password.html"))


@app.get("/applications-admin")
def applications_admin_page(staff=Depends(get_current_staff_optional)):
    gate = _staff_gate("/applications-admin", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "applications-admin.html"))


@app.get("/review-admin")
def review_admin_page(staff=Depends(get_current_staff_optional)):
    gate = _staff_gate("/review-admin", staff)
    if gate:
        return gate
    return FileResponse(os.path.join(WEB_DIR, "review-admin.html"))


@app.get("/review/{token}")
def review_reviewer_page(token: str):
    """Public, token-gated review page — no staff login. The token itself is
    the access control; an unknown/expired token is handled client-side by
    the page's own fetch against /api/review/projects/{token}."""
    return FileResponse(os.path.join(WEB_DIR, "review.html"))


@app.get("/", response_class=FileResponse)
def home_page():
    return FileResponse(os.path.join(WEB_DIR, "home.html"))


@app.get("/ops", response_class=HTMLResponse)
def internal_links():
    return """
    <html>
    <head><title>American Food & Beverage — Operations</title></head>
    <body style="font-family:-apple-system,sans-serif;max-width:640px;margin:60px auto;padding:0 24px;color:#241A10;">
      <h1>American Food &amp; Beverage — Operations</h1>
      <p>Internal tools. Pick where to go:</p>
      <ul style="line-height:2.2;font-size:1.05rem;">
        <li><a href="/order">Place / track an order</a> — customer-facing ordering site</li>
        <li><a href="/dashboard">Operations dashboard</a> — inventory, orders, shipping, reports (staff login required)</li>
        <li><a href="/production">Packing &amp; production</a> — packing manager assignments and packer daily logs (staff login required)</li>
        <li><a href="/applications-admin">Job applications</a> — review and update applicant status (staff login required)</li>
        <li><a href="/review-admin">Site review portal</a> — share workflow pages with reviewers, triage comments (staff login required)</li>
        <li><a href="/login">Staff login</a></li>
        <li><a href="/docs">API docs</a> — every endpoint, callable directly from the browser</li>
      </ul>
    </body>
    </html>
    """
SITE_DIR = SITE_DIR = os.path.join(os.path.dirname(__file__), "..", "afb-site")

app.mount("/store", StaticFiles(directory=SITE_DIR, html=True), name="store")