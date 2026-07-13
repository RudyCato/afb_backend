import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import customers, products, inventory, orders, packing, shipping, reports, production

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="American Food & Beverage — Operations API",
    description="Backend for inventory, packing, customers, shipping/delivery tracking and reporting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(packing.router)
app.include_router(shipping.router)
app.include_router(reports.router)
app.include_router(production.router)

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")

app.mount("/icons", StaticFiles(directory=os.path.join(WEB_DIR, "icons")), name="icons")


@app.get("/manifest.json")
def manifest():
    return FileResponse(os.path.join(WEB_DIR, "manifest.json"), media_type="application/manifest+json")


@app.get("/order", response_class=FileResponse)
def order_page():
    return FileResponse(os.path.join(WEB_DIR, "order.html"))


@app.get("/dashboard", response_class=FileResponse)
def dashboard_page():
    return FileResponse(os.path.join(WEB_DIR, "dashboard.html"))


@app.get("/production", response_class=FileResponse)
def production_page():
    return FileResponse(os.path.join(WEB_DIR, "production.html"))


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <head><title>American Food & Beverage — Operations</title></head>
    <body style="font-family:-apple-system,sans-serif;max-width:640px;margin:60px auto;padding:0 24px;color:#241A10;">
      <h1>American Food &amp; Beverage — Operations</h1>
      <p>This server is running and reachable on the network. Pick where to go:</p>
      <ul style="line-height:2.2;font-size:1.05rem;">
        <li><a href="/order">Place / track an order</a> — customer-facing ordering site</li>
        <li><a href="/dashboard">Operations dashboard</a> — inventory, orders, shipping, reports</li>
        <li><a href="/production">Packing &amp; production</a> — packing manager assignments and packer daily logs</li>
        <li><a href="/docs">API docs</a> — every endpoint, callable directly from the browser</li>
      </ul>
    </body>
    </html>
    """
