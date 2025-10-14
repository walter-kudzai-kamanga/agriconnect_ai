# weather_server/main.py
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from functools import lru_cache
import asyncio
import logging

# Optional: Redis cache (if REDIS_URL provided)
import redis.asyncio as redis

LOG = logging.getLogger("weather_mcp")
logging.basicConfig(level=logging.INFO)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
PORT = int(os.getenv("PORT", "8001"))
# Optional API key for clients calling this MCP server
CLIENT_API_KEY = os.getenv("MCP_CLIENT_API_KEY", None)
REDIS_URL = os.getenv("REDIS_URL", None)

app = FastAPI(title="Weather MCP Server", version="0.1")

redis = None  # will connect if REDIS_URL set

# ---------- Pydantic request/response models ----------

class WeatherRequest(BaseModel):
    lat: float = Field(..., example=-17.8067)
    lon: float = Field(..., example=31.0530)
    # optional: human-friendly name
    name: Optional[str] = None

class LocationOut(BaseModel):
    lat: float
    lon: float
    name: Optional[str] = None

class WeatherData(BaseModel):
    temperature_c: float
    feels_like_c: Optional[float]
    humidity_pct: Optional[int]
    wind_m_s: Optional[float]
    condition: Optional[str]

class MCPWeatherResponse(BaseModel):
    context_type: str = "weather"
    source: str
    timestamp: str
    location: LocationOut
    data: WeatherData
    meta: Dict[str, Any]

# ---------- Helper utilities ----------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def make_cache_key(lat: float, lon: float) -> str:
    # coarse rounding to reduce cache cardinality (e.g., 3 decimal places ~ 100m)
    return f"weather:{round(lat,3)}:{round(lon,3)}"

async def get_redis():
    global redis
    if REDIS_URL and redis is None:
        redis = redis.from_url(REDIS_URL)
    return redis

# Simple exponential backoff retry for external API calls
async def fetch_openweather(lat: float, lon: float, retries=3, backoff_base=0.5):
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(1, retries + 1):
            try:
                LOG.info("Fetching OpenWeather for %s,%s (attempt %s)", lat, lon, attempt)
                r = await client.get(OPENWEATHER_URL, params=params)
                r.raise_for_status()
                return r.json()
            except httpx.RequestError as e:
                LOG.warning("Request error: %s", e)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                LOG.warning("HTTP error %s: %s", status, e)
                if 400 <= status < 500:
                    # client error - don't retry
                    raise
            # backoff
            await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
    raise HTTPException(status_code=502, detail="Failed to fetch weather from upstream provider")

# Optional lightweight in-memory fallback cache (LRU) for single-process deployments
@lru_cache(maxsize=1024)
def in_memory_cache_get(key: str):
    # we store tuple (timestamp_iso, response_dict)
    return None  # We will handle LRU caching externally if needed

# ---------- Auth dependency ----------

async def verify_client_key(x_api_key: Optional[str] = Header(None)):
    if CLIENT_API_KEY is None:
        return True  # not enforcing
    if x_api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid client API key")
    return True

# ---------- Endpoints ----------

@app.on_event("startup")
async def startup_event():
    LOG.info("Starting Weather MCP Server")
    if REDIS_URL:
        await get_redis()
        LOG.info("Connected to Redis: %s", REDIS_URL)

@app.post("/query", response_model=MCPWeatherResponse)
async def query_weather(req: WeatherRequest, authorized=Depends(verify_client_key)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfigured: OPENWEATHER_API_KEY missing")

    cache_key = make_cache_key(req.lat, req.lon)
    # Try Redis cache first (if configured)
    if REDIS_URL:
        r = await get_redis()
        val = await r.get(cache_key)
        if val:
            LOG.info("Cache HIT (redis) for %s", cache_key)
            return MCPWeatherResponse.parse_raw(val)

    # Otherwise fetch upstream
    try:
        raw = await fetch_openweather(req.lat, req.lon)
    except HTTPException:
        # On upstream failure, optionally return a lower-fidelity response or raise
        raise

    # parse useful fields safely
    main = raw.get("main", {})
    wind = raw.get("wind", {})
    weather_arr = raw.get("weather") or []
    cond = weather_arr[0]["description"] if weather_arr else None

    response = {
        "context_type": "weather",
        "source": "openweathermap",
        "timestamp": now_iso(),
        "location": {"lat": req.lat, "lon": req.lon, "name": req.name},
        "data": {
            "temperature_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "humidity_pct": main.get("humidity"),
            "wind_m_s": wind.get("speed"),
            "condition": cond,
        },
        "meta": {
            "confidence": 0.9,
            "ttl_seconds": 300
        }
    }

    # Cache the response
    if REDIS_URL:
        r = await get_redis()
        await r.set(cache_key, MCPWeatherResponse(**response).json(), ex=response["meta"]["ttl_seconds"])
        LOG.info("Cached response in Redis for %s", cache_key)

    return MCPWeatherResponse(**response)


@app.get("/healthz")
async def health():
    return {"status": "ok", "time": now_iso()}
