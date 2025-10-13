from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models.schemas import HealthCheck

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

@app.get("/", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "message": "AgriConnect AI API is running"}

# Import and include routers
from app.mcp_server.mcp_tools import router as mcp_router
app.include_router(mcp_router, prefix="/api/v1/mcp", tags=["MCP Tools"])

@app.get("/api/v1/health")
async def root():
    return {"message": "AgriConnect AI Backend Service"}