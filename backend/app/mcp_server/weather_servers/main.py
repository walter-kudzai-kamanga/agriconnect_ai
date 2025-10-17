# weather_server/main.py
import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Header, Depends, status, Query
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger("weather_mcp")

# Configuration
class Config:
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    PORT = int(os.getenv("PORT", "8001"))
    CLIENT_API_KEY = os.getenv("MCP_CLIENT_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # API Settings
    OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    OPENWEATHER_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
    
    # Cache settings
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    MAX_CACHE_TTL = 3600     # 1 hour
    MIN_CACHE_TTL = 60       # 1 minute
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 60  # requests per minute
    RATE_LIMIT_WINDOW = 60    # seconds

config = Config()

# ---------- Models ----------

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, example=40.7128)
    lon: float = Field(..., ge=-180, le=180, example=-74.0060)
    name: Optional[str] = Field(None, example="Marondera")
    country: Optional[str] = Field(None, example="Zimbabwe")

class WeatherRequest(BaseModel):
    location: Location
    force_refresh: bool = Field(False, description="Bypass cache and fetch fresh data")
    units: str = Field("metric", pattern="^(metric|imperial|standard)$")
    cache_ttl: Optional[int] = Field(None, ge=60, le=3600, description="Custom cache TTL in seconds")

class WeatherData(BaseModel):
    temperature: float = Field(..., description="Temperature in requested units")
    feels_like: float = Field(..., description="Feels-like temperature")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., description="Wind speed in requested units")
    wind_direction: Optional[int] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    visibility: Optional[int] = Field(None, description="Visibility in meters")
    cloudiness: int = Field(..., ge=0, le=100, description="Cloudiness percentage")
    condition: str = Field(..., description="Weather condition")
    condition_id: int = Field(..., description="OpenWeather condition ID")
    icon: Optional[str] = Field(None, description="Weather icon code")

class WeatherResponse(BaseModel):
    context_type: str = "weather"
    source: str = "openweathermap"
    timestamp: str
    location: Location
    data: WeatherData
    units: str
    meta: Dict[str, Any] = Field(default_factory=dict)

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid ISO timestamp format')

class BulkWeatherRequest(BaseModel):
    locations: List[Location] = Field(..., max_items=10)
    units: str = Field("metric", pattern="^(metric|imperial|standard)$")

class BulkWeatherResponse(BaseModel):
    results: List[WeatherResponse]
    meta: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
    uptime: float
    version: str = "1.0.0"

# ---------- Services ----------

class WeatherService:
    def __init__(self):
        self.client = None
        self.redis_pool = None
        self.start_time = time.time()
    
    async def initialize(self):
        """Initialize HTTP client and Redis connection"""
        timeout = httpx.Timeout(10.0, connect=15.0)
        self.client = httpx.AsyncClient(timeout=timeout)
        
        if config.REDIS_URL:
            try:
                self.redis_pool = ConnectionPool.from_url(
                    config.REDIS_URL,
                    max_connections=20,
                    decode_responses=True
                )
                LOG.info("Redis connection pool initialized")
            except Exception as e:
                LOG.warning("Failed to initialize Redis: %s", e)
                self.redis_pool = None
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
        if self.redis_pool:
            await self.redis_pool.disconnect()
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    async def get_redis(self) -> Optional[redis.Redis]:
        if self.redis_pool:
            return redis.Redis(connection_pool=self.redis_pool)
        return None
    
    def make_cache_key(self, lat: float, lon: float, units: str) -> str:
        return f"weather:{round(lat, 4)}:{round(lon, 4)}:{units}"
    
    async def fetch_live_weather(self, lat: float, lon: float, units: str) -> Dict[str, Any]:
        """Fetch live weather data from OpenWeatherMap"""
        if not config.OPENWEATHER_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenWeatherMap API key not configured"
            )
        
        params = {
            "lat": lat,
            "lon": lon,
            "appid": config.OPENWEATHER_API_KEY,
            "units": units
        }
        
        for attempt in range(3):
            try:
                LOG.info("Fetching live weather data for %s,%s (attempt %d)", lat, lon, attempt + 1)
                
                response = await self.client.get(config.OPENWEATHER_URL, params=params)
                
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid OpenWeatherMap API key"
                    )
                elif response.status_code == 429:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Rate limit exceeded for weather service"
                    )
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Location not found"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # Validate response structure
                if not all(key in data for key in ['main', 'weather', 'wind']):
                    raise ValueError("Invalid response structure from weather API")
                
                return data
                
            except httpx.TimeoutException:
                LOG.warning("Timeout fetching weather data (attempt %d)", attempt + 1)
                if attempt == 2:
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail="Weather service timeout"
                    )
            except httpx.RequestError as e:
                LOG.error("Request error: %s", e)
                if attempt == 2:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Weather service unavailable"
                    )
            except httpx.HTTPStatusError as e:
                LOG.error("HTTP error %s: %s", e.response.status_code, e)
                if attempt == 2:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Weather service error"
                    )
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch weather data after multiple attempts"
        )
    
    async def get_weather(self, request: WeatherRequest) -> WeatherResponse:
        """Get weather data with caching support"""
        lat, lon = request.location.lat, request.location.lon
        cache_key = self.make_cache_key(lat, lon, request.units)
        cache_ttl = request.cache_ttl or config.DEFAULT_CACHE_TTL
        
        # Try cache first unless force_refresh is True
        if not request.force_refresh:
            cached_data = await self._get_cached_weather(cache_key)
            if cached_data:
                LOG.info("Cache hit for %s", cache_key)
                return cached_data
        
        # Fetch live data
        LOG.info("Fetching live weather data for %s,%s", lat, lon)
        raw_data = await self.fetch_live_weather(lat, lon, request.units)
        
        # Parse response
        weather_response = self._parse_weather_response(raw_data, request.location, request.units)
        
        # Cache the response
        await self._cache_weather(cache_key, weather_response, cache_ttl)
        
        return weather_response
    
    async def _get_cached_weather(self, cache_key: str) -> Optional[WeatherResponse]:
        """Get weather data from cache"""
        redis_client = await self.get_redis()
        if not redis_client:
            return None
        
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return WeatherResponse.parse_raw(cached)
        except Exception as e:
            LOG.warning("Redis cache read failed: %s", e)
        
        return None
    
    async def _cache_weather(self, cache_key: str, response: WeatherResponse, ttl: int):
        """Cache weather data"""
        redis_client = await self.get_redis()
        if not redis_client:
            return
        
        try:
            await redis_client.setex(
                cache_key,
                timedelta(seconds=ttl),
                response.json()
            )
            LOG.info("Cached weather data for %s (TTL: %ds)", cache_key, ttl)
        except Exception as e:
            LOG.warning("Failed to cache weather data: %s", e)
    
    def _parse_weather_response(self, raw_data: Dict, location: Location, units: str) -> WeatherResponse:
        """Parse OpenWeatherMap response into standardized format"""
        main = raw_data.get('main', {})
        weather = raw_data.get('weather', [{}])[0]
        wind = raw_data.get('wind', {})
        
        # Determine unit labels for metadata
        unit_labels = {
            "metric": {"temp": "°C", "speed": "m/s"},
            "imperial": {"temp": "°F", "speed": "mph"},
            "standard": {"temp": "K", "speed": "m/s"}
        }
        
        weather_data = WeatherData(
            temperature=main.get('temp', 0),
            feels_like=main.get('feels_like', 0),
            humidity=main.get('humidity', 0),
            pressure=main.get('pressure', 0),
            wind_speed=wind.get('speed', 0),
            wind_direction=wind.get('deg'),
            visibility=raw_data.get('visibility'),
            cloudiness=raw_data.get('clouds', {}).get('all', 0),
            condition=weather.get('description', ''),
            condition_id=weather.get('id', 0),
            icon=weather.get('icon')
        )
        
        return WeatherResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            location=location,
            data=weather_data,
            units=units,
            meta={
                "cache_ttl": config.DEFAULT_CACHE_TTL,
                "confidence": 0.95,
                "units_label": unit_labels.get(units, {}),
                "city_id": raw_data.get('id'),
                "timezone": raw_data.get('timezone'),
                "sunrise": raw_data.get('sys', {}).get('sunrise'),
                "sunset": raw_data.get('sys', {}).get('sunset')
            }
        )
    
    async def get_bulk_weather(self, request: BulkWeatherRequest) -> BulkWeatherResponse:
        """Get weather for multiple locations concurrently"""
        tasks = []
        for location in request.locations:
            weather_request = WeatherRequest(
                location=location,
                units=request.units,
                force_refresh=False  # Allow caching for bulk requests
            )
            tasks.append(self.get_weather(weather_request))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                LOG.error("Error fetching weather for location %d: %s", i, result)
                # You could create an error response here if needed
                continue
            processed_results.append(result)
        
        return BulkWeatherResponse(
            results=processed_results,
            meta={
                "total_locations": len(request.locations),
                "successful_results": len(processed_results),
                "failed_results": len(request.locations) - len(processed_results)
            }
        )
    
    async def clear_cache(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Clear cache for specific location or all weather data"""
        redis_client = await self.get_redis()
        if not redis_client:
            return {"cleared": 0, "message": "Redis not configured"}
        
        try:
            if lat is not None and lon is not None:
                # Clear specific location for all unit types
                pattern = f"weather:{round(lat, 4)}:{round(lon, 4)}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                return {"cleared": len(keys), "pattern": pattern}
            else:
                # Clear all weather cache
                keys = await redis_client.keys("weather:*")
                if keys:
                    await redis_client.delete(*keys)
                return {"cleared": len(keys), "pattern": "weather:*"}
        except Exception as e:
            LOG.error("Failed to clear cache: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cache clearance failed"
            )
    
    async def health_check(self) -> HealthResponse:
        """Comprehensive health check"""
        services = {
            "openweathermap": "unknown",
            "redis": "not configured"
        }
        
        # Check OpenWeatherMap
        try:
            test_params = {"lat": 0, "lon": 0, "appid": config.OPENWEATHER_API_KEY}
            response = await self.client.get(config.OPENWEATHER_URL, params=test_params)
            services["openweathermap"] = "healthy" if response.status_code != 401 else "invalid_key"
        except Exception as e:
            services["openweathermap"] = f"unhealthy: {str(e)}"
        
        # Check Redis
        if self.redis_pool:
            try:
                redis_client = await self.get_redis()
                await redis_client.ping()
                services["redis"] = "healthy"
            except Exception as e:
                services["redis"] = f"unhealthy: {str(e)}"
        
        return HealthResponse(
            status="healthy" if all("healthy" in status for status in services.values()) else "degraded",
            timestamp=datetime.now(timezone.utc).isoformat(),
            services=services,
            uptime=self.get_uptime()
        )

# ---------- FastAPI App Setup ----------

weather_service = WeatherService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await weather_service.initialize()
    LOG.info("Weather MCP Server started successfully")
    yield
    # Shutdown
    await weather_service.shutdown()
    LOG.info("Weather MCP Server shutdown complete")

app = FastAPI(
    title="Weather MCP Server",
    description="High-performance weather data server with live data and caching",
    version="1.0.0",
    lifespan=lifespan
)

# ---------- Dependencies ----------

async def verify_client_key(x_api_key: Optional[str] = Header(None)) -> bool:
    if not config.CLIENT_API_KEY:
        return True
    if x_api_key != config.CLIENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True

# ---------- Endpoints ----------

@app.post("/weather", response_model=WeatherResponse)
async def get_weather(
    request: WeatherRequest,
    authorized: bool = Depends(verify_client_key)
):
    """Get current weather data for a location"""
    return await weather_service.get_weather(request)

@app.post("/weather/bulk", response_model=BulkWeatherResponse)
async def get_bulk_weather(
    request: BulkWeatherRequest,
    authorized: bool = Depends(verify_client_key)
):
    """Get weather data for multiple locations"""
    if len(request.locations) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 locations allowed per request"
        )
    return await weather_service.get_bulk_weather(request)

@app.delete("/cache")
async def clear_weather_cache(
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lon: Optional[float] = Query(None, ge=-180, le=180),
    authorized: bool = Depends(verify_client_key)
):
    """Clear weather cache for specific location or all cached data"""
    return await weather_service.clear_cache(lat, lon)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    return await weather_service.health_check()

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Weather MCP Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "weather": "/weather",
            "bulk_weather": "/weather/bulk",
            "health": "/health",
            "cache_management": "/cache"
        }
    }

# ---------- Main Entry Point ----------

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level="info",
        access_log=True
    )