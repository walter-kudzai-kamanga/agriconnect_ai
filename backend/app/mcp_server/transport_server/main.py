# transport_server/main.py
import os
import asyncio
import math
import logging
from typing import Optional, Dict, Any, List

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import aioredis
import httpx

LOG = logging.getLogger("transport_mcp")
logging.basicConfig(level=logging.INFO)

# Config from environment
PORT = int(os.getenv("PORT", "8003"))
CLIENT_API_KEY = os.getenv("MCP_CLIENT_API_KEY", None)
REDIS_URL = os.getenv("REDIS_URL", None)
TELEMATICS_API = os.getenv("TELEMATICS_API", None)  # optional external telematics provider

app = FastAPI(title="Transport MCP Server", version="0.2")
redis = None

# ----------------- Models -----------------
class LatLon(BaseModel):
    lat: float
    lon: float

class TransportRequest(BaseModel):
    farmer_location: LatLon
    required_capacity_kg: float = Field(..., example=500.0)
    max_wait_minutes: Optional[int] = Field(60, example=60)

class TruckInfo(BaseModel):
    id: str
    location: LatLon
    capacity_kg: float
    status: str  # available | busy | maintenance
    eta_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    last_seen: Optional[str] = None

class MCPTransportResponse(BaseModel):
    context_type: str = "transport"
    source: str
    timestamp: str
    location: LatLon
    data: Dict[str, Any]
    meta: Dict[str, Any]

# ----------------- Helpers -----------------
def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def get_redis():
    global redis
    if REDIS_URL and redis is None:
        redis = await aioredis.from_url(REDIS_URL)
    return redis

def haversine_km(a_lat, a_lon, b_lat, b_lon):
    # haversine formula
    R = 6371.0  # km
    phi1 = math.radians(a_lat)
    phi2 = math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dlambda = math.radians(b_lon - a_lon)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

async def fetch_telematics_trucks():
    """
    Optionally fetch live trucks from telematics provider.
    Must return a list of dicts with keys: id, lat, lon, capacity_kg, status, last_seen
    """
    if not TELEMATICS_API:
        return []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(TELEMATICS_API)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        LOG.warning("Telematics fetch failed: %s", e)
        return []

# Simple mock fleet for MVP; replace with DB or telematics
MOCK_TRUCKS = [
    {"id": "T-001", "lat": -17.800, "lon": 31.050, "capacity_kg": 2000, "status": "available"},
    {"id": "T-002", "lat": -17.760, "lon": 31.020, "capacity_kg": 800,  "status": "available"},
    {"id": "T-003", "lat": -18.970, "lon": 32.640, "capacity_kg": 1500, "status": "busy"},
]

def compute_eta_minutes(distance_km, avg_speed_kmh=40.0):
    if distance_km <= 0:
        return 0
    hours = distance_km / avg_speed_kmh
    return int(hours * 60) + 5  # add handling time buffer

def make_cache_key(lat: float, lon: float, capacity: float):
    return f"transport:{round(lat,3)}:{round(lon,3)}:{int(capacity)}"

# ----------------- Auth -----------------
async def verify_client_key(x_api_key: Optional[str] = Header(None)):
    if CLIENT_API_KEY is None:
        return True
    if x_api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid client API key")
    return True

# ----------------- Core logic -----------------
async def get_fleet():
    # prefer telematics if available
    tele = await fetch_telematics_trucks()
    if tele:
        return tele
    # adapt mock trucks to unified shape
    return [
        {
            "id": t["id"],
            "lat": t.get("lat"),
            "lon": t.get("lon"),
            "capacity_kg": t.get("capacity_kg"),
            "status": t.get("status"),
            "last_seen": now_iso()
        } for t in MOCK_TRUCKS
    ]

async def find_available_trucks(farmer_lat: float, farmer_lon: float, required_capacity: float):
    fleet = await get_fleet()
    candidates = []
    for t in fleet:
        if t["status"] != "available":
            continue
        if t["capacity_kg"] < required_capacity:
            continue
        dist = haversine_km(farmer_lat, farmer_lon, t["lat"], t["lon"])
        eta = compute_eta_minutes(dist)
        candidates.append({
            "id": t["id"],
            "location": {"lat": t["lat"], "lon": t["lon"]},
            "capacity_kg": t["capacity_kg"],
            "status": t["status"],
            "distance_km": round(dist, 2),
            "eta_minutes": eta,
            "last_seen": t.get("last_seen")
        })
    # sort by ETA ascending, capacity descending
    candidates.sort(key=lambda x: (x["eta_minutes"], -x["capacity_kg"]))
    return candidates

# ----------------- Endpoints -----------------
@app.on_event("startup")
async def startup_event():
    LOG.info("Starting Transport MCP Server")
    if REDIS_URL:
        await get_redis()
        LOG.info("Connected to Redis")

@app.post("/query", response_model=MCPTransportResponse)
async def query_transport(req: TransportRequest, authorized=Depends(verify_client_key)):
    lat = req.farmer_location.lat
    lon = req.farmer_location.lon
    cache_key = make_cache_key(lat, lon, req.required_capacity_kg)
    # try cache
    if REDIS_URL:
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            LOG.info("Cache hit transport %s", cache_key)
            return MCPTransportResponse.parse_raw(cached)

    candidates = await find_available_trucks(lat, lon, req.required_capacity_kg)
    selected = candidates[0] if candidates else None

    response = {
        "context_type": "transport",
        "source": "mock_fleet_v1" if not TELEMATICS_API else "telematics_provider",
        "timestamp": now_iso(),
        "location": {"lat": lat, "lon": lon},
        "data": {"available_trucks": candidates, "selected_truck": selected},
        "meta": {"confidence": 0.9 if selected else 0.3, "ttl_seconds": 120, "schema_version": "1.0"}
    }

    if REDIS_URL:
        r = await get_redis()
        await r.set(cache_key, MCPTransportResponse(**response).json(), ex=response["meta"]["ttl_seconds"])
    return MCPTransportResponse(**response)

@app.post("/batch_query", response_model=List[MCPTransportResponse])
async def batch_query(reqs: List[TransportRequest], authorized=Depends(verify_client_key)):
    tasks = [query_transport(r) for r in reqs]
    results = await asyncio.gather(*tasks)
    return results

@app.get("/healthz")
async def health():
    return {"status":"ok", "time": now_iso()}

# ----------------- Optional: WebSocket for real-time updates -----------------
class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active:
            del self.active[client_id]

    async def send_update(self, client_id: str, message: dict):
        ws = self.active.get(client_id)
        if ws:
            await ws.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(client_id)
