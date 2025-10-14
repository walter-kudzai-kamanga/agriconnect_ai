# market_server/main.py
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import logging
import aioredis

LOG = logging.getLogger("market_mcp")
logging.basicConfig(level=logging.INFO)

PORT = int(os.getenv("PORT", "8002"))
CLIENT_API_KEY = os.getenv("MCP_CLIENT_API_KEY", None)
REDIS_URL = os.getenv("REDIS_URL", None)

app = FastAPI(title="Market MCP Server", version="0.1")
redis = None

# ---------- Models ----------
class MarketRequest(BaseModel):
    product: str = Field(..., example="tomatoes")
    location: Optional[Dict[str, float]] = None  # {"lat": -17.8, "lon": 31.0}
    radius_km: Optional[int] = Field(50, example=50)

class MarketEntry(BaseModel):
    market_name: str
    price_local: float
    currency: str
    last_updated: Optional[str] = None

class MCPMarketResponse(BaseModel):
    context_type: str = "market"
    source: str
    timestamp: str
    location: Optional[Dict[str, float]] = None
    data: Dict[str, Any]
    meta: Dict[str, Any]

# ---------- Helpers ----------
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def make_cache_key(product: str, lat: Optional[float], lon: Optional[float], radius: int):
    if lat is None or lon is None:
        return f"market:{product.lower()}:global"
    return f"market:{product.lower()}:{round(lat,3)}:{round(lon,3)}:{radius}"

async def get_redis():
    global redis
    if REDIS_URL and redis is None:
        redis = await aioredis.from_url(REDIS_URL)
    return redis

async def verify_client_key(x_api_key: Optional[str] = Header(None)):
    if CLIENT_API_KEY is None:
        return True
    if x_api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid client API key")
    return True

# ---------- Mock / Upstream Data Fetchers ----------
# In production you'd call real market data APIs or aggregator.
async def fetch_market_prices_from_provider(product: str, lat: Optional[float], lon: Optional[float], radius_km: int):
    # Simulate variable latency
    await asyncio.sleep(0.2)
    # Mock dataset: in production, query aggregator or national market API
    MOCK = {
        "tomatoes": [
            {"market_name": "Mbare Musika", "price_local": 1.5, "currency": "USD", "lat": -17.825, "lon": 31.030},
            {"market_name": "Avondale Market", "price_local": 1.4, "currency": "USD", "lat": -17.790, "lon": 31.060},
            {"market_name": "Mutare Central", "price_local": 1.6, "currency": "USD", "lat": -18.970, "lon": 32.640},
        ],
        "maize": [
            {"market_name": "Mbare Musika", "price_local": 0.9, "currency": "USD", "lat": -17.825, "lon": 31.030},
        ],
    }
    items = MOCK.get(product.lower(), [])
    # naive radius filter (could use haversine)
    if lat is not None and lon is not None:
        # keep all for MVP; production filter by distance
        pass
    return items

# ---------- Endpoints ----------
@app.on_event("startup")
async def startup_event():
    LOG.info("Starting Market MCP Server")
    if REDIS_URL:
        await get_redis()
        LOG.info("Connected to Redis")

@app.post("/query", response_model=MCPMarketResponse)
async def query_market(req: MarketRequest, authorized=Depends(verify_client_key)):
    cache_key = make_cache_key(req.product, None if req.location is None else req.location.get("lat"),
                               None if req.location is None else req.location.get("lon"), req.radius_km)
    # Try Redis cache
    if REDIS_URL:
        r = await get_redis()
        val = await r.get(cache_key)
        if val:
            LOG.info("Redis cache hit for %s", cache_key)
            return MCPMarketResponse.parse_raw(val)

    try:
        entries = await fetch_market_prices_from_provider(req.product, 
                                                          None if req.location is None else req.location.get("lat"),
                                                          None if req.location is None else req.location.get("lon"),
                                                          req.radius_km)
    except Exception as e:
        LOG.exception("Upstream market fetch failed")
        raise HTTPException(status_code=502, detail="Failed to fetch market data")

    # Build response
    data = {"product": req.product.lower(), "markets": entries}
    best_market = None
    if entries:
        best_market = max(entries, key=lambda x: x["price_local"])  # highest price (seller's perspective)
    response = {
        "context_type": "market",
        "source": "mock_provider_v1",
        "timestamp": now_iso(),
        "location": req.location,
        "data": {"product": req.product.lower(), "markets": entries, "best_market": best_market},
        "meta": {"confidence": 0.85, "ttl_seconds": 600, "schema_version": "1.0"}
    }

    if REDIS_URL:
        r = await get_redis()
        await r.set(cache_key, MCPMarketResponse(**response).json(), ex=response["meta"]["ttl_seconds"])
        LOG.info("Cached market response for %s", cache_key)

    return MCPMarketResponse(**response)

@app.post("/batch_query", response_model=List[MCPMarketResponse])
async def batch_query_markets(reqs: List[MarketRequest], authorized=Depends(verify_client_key)):
    # Simple parallelization
    tasks = [query_market(r) for r in reqs]
    results = await asyncio.gather(*tasks)
    return results

@app.get("/healthz")
async def health():
    return {"status": "ok", "time": now_iso()}
