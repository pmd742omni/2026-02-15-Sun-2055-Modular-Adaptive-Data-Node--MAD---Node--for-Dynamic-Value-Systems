import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="MADN Offline Hub API",
    description="Offline-first API running locally on the Raspberry Pi 4 Vault hub.",
    version="1.0.0"
)

# Resolve paths relatively to support portability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/api/health")
async def get_health():
    """Local node health check endpoint."""
    return {
        "status": "healthy",
        "mode": "offline-first",
        "database": "sqlite_connected"
    }

# Serve frontend SPA at root level
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
