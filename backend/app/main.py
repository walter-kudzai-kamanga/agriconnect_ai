from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.models.schemas import HealthCheck
import os
from pathlib import Path
from app.mcp_server.ussd_router import router as ussd_router
# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriConnect AI API",
    description="Farm-to-Market Logistics Intelligence Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

# Create public directory if it doesn't exist
PUBLIC_DIR.mkdir(exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


app.include_router(ussd_router, prefix="/api", tags=["USSD"])
# Serve the main HTML file for the root route
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(PUBLIC_DIR / "index.html")

# Health check endpoint at /api/health
@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "message": "AgriConnect AI API is running"}

# Import and include routers
from app.mcp_server.mcp_tools import router as mcp_router

#from app.admin.routes import router as admin_router

app.include_router(mcp_router, prefix="/api/v1/mcp", tags=["MCP Tools"])
#app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin Dashboard"])

# API health endpoint
@app.get("/api/v1/health")
async def root():
    return {"message": "AgriConnect AI Backend Service"}

# Catch-all route to serve the frontend (for SPA routing)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    file_path = PUBLIC_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    # For any other route, serve the main index.html (for SPA routing)
    return FileResponse(PUBLIC_DIR / "index.html")