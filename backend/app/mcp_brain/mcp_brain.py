import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from database import get_db, engine, Base, SessionLocal
    from mcp_server.mcp_tools import router as mcp_tools_router, spoilage_predictor
    from mcp_server.ussd_router import router as ussd_router
except ImportError:
    # Fallback - create minimal stubs
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine("sqlite:///./agriconnect.db")
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    mcp_tools_router = None
    ussd_router = None
    
    class SpoilagePredictorStub:
        def predict_risk(self, **kwargs):
            return 0.15
    
    spoilage_predictor = SpoilagePredictorStub()

# Try to import Redis for caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - caching disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger("mcp_brain")

# Configuration
class Config:
    SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # MCP Server URLs - use environment variables for production
    WEATHER_SERVICE_URL = os.getenv("WEATHER_SERVICE_URL", "http://localhost:8001")
    MARKET_SERVICE_URL = os.getenv("MARKET_SERVICE_URL", "http://localhost:8002")
    TRANSPORT_SERVICE_URL = os.getenv("TRANSPORT_SERVICE_URL", "http://localhost:8003")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Cache settings
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    MAX_RETRY_ATTEMPTS = 3
    REQUEST_TIMEOUT = 10.0

config = Config()

# User model (in production, use a database)
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[str] = ["user"]

# Mock user database (replace with real DB in production)
fake_users_db = {
    "walter": {
        "username": "walter",
        "full_name": "Walter Test User",
        "email": "walter@example.com",
        "hashed_password": "walehashed",
        "disabled": False,
        "roles": ["user", "admin"]
    },
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
        "roles": ["user", "admin"]
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": False,
        "roles": ["user"]
    }
}

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# MCP Service Client with retry logic and circuit breaker
class MCPServiceClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.http_client = None
        self.redis_client = None
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
    async def initialize(self):
        """Initialize HTTP client and Redis"""
        timeout = httpx.Timeout(config.REQUEST_TIMEOUT, connect=15.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        if REDIS_AVAILABLE and config.REDIS_URL:
            try:
                self.redis_client = redis.from_url(config.REDIS_URL)
                await self.redis_client.ping()
                LOG.info(f"{self.service_name} Redis connected")
            except Exception as e:
                LOG.warning(f"{self.service_name} Redis failed: {e}")
                self.redis_client = None
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
    
    def check_circuit_breaker(self):
        """Check if circuit breaker should be opened"""
        if self.failure_count >= 5:
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) < 30:  # 30 second cooldown
                self.circuit_open = True
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"{self.service_name} circuit breaker open - too many failures"
                )
            else:
                # Reset after cooldown
                self.failure_count = 0
                self.circuit_open = False
    
    async def query(self, endpoint: str, data: dict, headers: dict = None) -> Dict[str, Any]:
        """Query MCP service with retry logic and caching"""
        self.check_circuit_breaker()
        
        # Try cache first
        cache_key = f"{self.service_name}:{endpoint}:{hash(str(data))}"
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    LOG.info(f"Cache hit for {self.service_name}/{endpoint}")
                    import json
                    return json.loads(cached)
            except Exception as e:
                LOG.warning(f"Cache read failed: {e}")
        
        # Query service with retry
        for attempt in range(config.MAX_RETRY_ATTEMPTS):
            try:
                LOG.info(f"Querying {self.service_name}/{endpoint} (attempt {attempt + 1})")
                
                response = await self.http_client.post(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers=headers or {}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Cache successful response
                    if self.redis_client:
                        try:
                            import json
                            await self.redis_client.setex(
                                cache_key,
                                timedelta(seconds=config.DEFAULT_CACHE_TTL),
                                json.dumps(result)
                            )
                        except Exception as e:
                            LOG.warning(f"Cache write failed: {e}")
                    
                    # Reset failure count on success
                    self.failure_count = 0
                    return result
                
                response.raise_for_status()
                
            except httpx.TimeoutException:
                LOG.warning(f"{self.service_name} timeout (attempt {attempt + 1})")
                if attempt == config.MAX_RETRY_ATTEMPTS - 1:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail=f"{self.service_name} timeout after {config.MAX_RETRY_ATTEMPTS} attempts"
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                LOG.error(f"{self.service_name} error: {e}")
                if attempt == config.MAX_RETRY_ATTEMPTS - 1:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"{self.service_name} unavailable: {str(e)}"
                    )
                await asyncio.sleep(2 ** attempt)

# Initialize MCP service clients
weather_client = MCPServiceClient(config.WEATHER_SERVICE_URL, "weather")
market_client = MCPServiceClient(config.MARKET_SERVICE_URL, "market")
transport_client = MCPServiceClient(config.TRANSPORT_SERVICE_URL, "transport")

# Auth functions
def verify_password(plain_password, hashed_password):
    # In production, use proper password hashing like bcrypt
    return plain_password + "hashed" == hashed_password

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return User(**user_dict)
    return None

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, fake_db[username]["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, roles=payload.get("roles", []))
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    async def check_rate_limit(self, client_id: str):
        """Simple in-memory rate limiting"""
        now = time.time()
        window_start = now - config.RATE_LIMIT_WINDOW
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= config.RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        self.requests[client_id].append(now)

rate_limiter = RateLimiter()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await weather_client.initialize()
    await market_client.initialize()
    await transport_client.initialize()
    LOG.info("MCP Brain started - all services initialized")
    yield
    # Shutdown
    await weather_client.shutdown()
    await market_client.shutdown()
    await transport_client.shutdown()
    LOG.info("MCP Brain shutdown complete")

# FastAPI app
app = FastAPI(
    title="MCP Brain API",
    version="2.0.0",
    description="Intelligent farm-to-market orchestration with MCP integration",
    lifespan=lifespan
)

# Enable CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers if available
if mcp_tools_router:
    app.include_router(mcp_tools_router, prefix="/api/v1/mcp", tags=["MCP Tools"])
if ussd_router:
    app.include_router(ussd_router, prefix="/api", tags=["USSD"])

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Test endpoint to show available users
@app.get("/test-users")
async def get_test_users():
    """Endpoint to show available test users for development"""
    users_info = []
    for username, user_data in fake_users_db.items():
        users_info.append({
            "username": username,
            "password_hint": user_data["hashed_password"].replace("hashed", ""),
            "roles": user_data["roles"],
            "disabled": user_data["disabled"]
        })
    return {
        "test_users": users_info,
        "note": "For testing, use username 'walter' with password 'wale'"
    }

# Protected endpoint
@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Test endpoint to show available users
@app.get("/test-users")
async def get_test_users():
    """Endpoint to show available test users for development"""
    users_info = []
    for username, user_data in fake_users_db.items():
        users_info.append({
            "username": username,
            "password_hint": user_data["hashed_password"].replace("hashed", ""),
            "roles": user_data["roles"],
            "disabled": user_data["disabled"]
        })
    return {
        "test_users": users_info,
        "note": "For testing, use username 'walter' with password 'wale'"
    }

# Simple query endpoint for quick testing
@app.post("/query/simple")
async def simple_query(
    request: Request,
    product: str,
    lat: float = -17.825,
    lon: float = 31.030,
    current_user: User = Depends(get_current_active_user)
):
    """Simplified query for quick testing"""
    location = {"lat": lat, "lon": lon}
    return await query_mcp_contexts(request, lat, lon, product, 500.0, location, current_user)

# Enhanced MCP Query Endpoint
@app.post("/query")
async def query_mcp_contexts(
    request: Request,
    lat: float,
    lon: float,
    product: str,
    capacity: float,
    location: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Intelligent multi-context query with MCP integration.
    """
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(current_user.username)
        
        # Query all MCP services concurrently
        weather_task = weather_client.query(
            "weather",
            {
                "location": {"lat": lat, "lon": lon},
                "units": "metric"
            }
        )
        
        market_task = market_client.query(
            "market/query",
            {
                "product": product,
                "location": {"lat": lat, "lon": lon},
                "radius_km": 50
            }
        )
        
        transport_task = transport_client.query(
            "transport/query",
            {
                "pickup_location": {"lat": lat, "lon": lon},
                "required_capacity_kg": capacity,
                "perishable": product.lower() in ["tomatoes", "vegetables", "fruits"]
            }
        )
        
        # Wait for all responses
        weather, market, transport = await asyncio.gather(
            weather_task, market_task, transport_task,
            return_exceptions=True
        )
        
        # Handle partial failures gracefully
        if isinstance(weather, Exception):
            LOG.error(f"Weather service failed: {weather}")
            weather = {"error": str(weather), "status": "unavailable"}
        
        if isinstance(market, Exception):
            LOG.error(f"Market service failed: {market}")
            market = {"error": str(market), "status": "unavailable"}
        
        if isinstance(transport, Exception):
            LOG.error(f"Transport service failed: {transport}")
            transport = {"error": str(transport), "status": "unavailable"}
        
        # Intelligent analysis
        analysis = await analyze_mcp_data(weather, market, transport, product)
        
        return {
            "status": "success",
            "user": current_user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "weather": weather,
                "market": market,
                "transport": transport
            },
            "analysis": analysis,
            "meta": {
                "services_queried": ["weather", "market", "transport"],
                "response_time_ms": int((time.time() - request.state.start_time) * 1000) if hasattr(request.state, 'start_time') else 0
            }
        }
    
    except Exception as e:
        LOG.error(f"MCP query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP query failed: {str(e)}"
        )

async def analyze_mcp_data(weather: dict, market: dict, transport: dict, product: str) -> dict:
    """Intelligent analysis of MCP data"""
    analysis = {
        "weather_score": 0.5,
        "market_score": 0.5,
        "transport_score": 0.5,
        "combined_score": 0.5,
        "recommendation": "Insufficient data",
        "insights": []
    }
    
    # Weather analysis
    if "error" not in weather and "data" in weather:
        weather_data = weather.get("data", {})
        condition = weather_data.get("condition", "").lower()
        temp = weather_data.get("temperature", 25)
        
        if condition in ["rain", "storm", "thunderstorm"]:
            analysis["weather_score"] = 0.3
            analysis["insights"].append("⚠️ Poor weather conditions - consider delaying")
        elif temp > 30:
            analysis["weather_score"] = 0.6
            analysis["insights"].append("🌡️ High temperature - use refrigerated transport")
        else:
            analysis["weather_score"] = 1.0
            analysis["insights"].append("✅ Good weather conditions")
    
    # Market analysis
    if "error" not in market and "prices" in market:
        prices = market.get("prices", [])
        if prices:
            avg_price = sum(p.get("price", 0) for p in prices) / len(prices)
            analysis["market_score"] = min(avg_price / 3.0, 1.0)  # Normalize
            analysis["insights"].append(f"💰 Average market price: ${avg_price:.2f}/kg")
    
    # Transport analysis
    if "error" not in transport and "available_vehicles" in transport:
        vehicles = transport.get("available_vehicles", [])
        if vehicles:
            analysis["transport_score"] = 1.0
            best_vehicle = vehicles[0]
            analysis["insights"].append(
                f"🚚 {len(vehicles)} vehicles available - Best: {best_vehicle.get('vehicle_type', 'truck')}"
            )
        else:
            analysis["transport_score"] = 0.2
            analysis["insights"].append("⚠️ Limited transport availability")
    
    # Spoilage prediction
    if product.lower() in ["tomatoes", "vegetables", "fruits"]:
        spoilage_risk = spoilage_predictor.predict_risk(
            crop_type=product,
            estimated_duration=120,  # Default 2 hours
            weather_conditions={"temperature": weather.get("data", {}).get("temperature", 25)}
        )
        analysis["spoilage_risk"] = spoilage_risk
        if spoilage_risk > 0.3:
            analysis["insights"].append(f"🔴 High spoilage risk: {spoilage_risk*100:.1f}%")
    
    # Combined score
    analysis["combined_score"] = (
        analysis["weather_score"] +
        analysis["market_score"] +
        analysis["transport_score"]
    ) / 3
    
    # Generate recommendation
    if analysis["combined_score"] > 0.8:
        analysis["recommendation"] = "✅ Excellent conditions - Proceed immediately"
    elif analysis["combined_score"] > 0.6:
        analysis["recommendation"] = "🟢 Good conditions - Proceed with standard precautions"
    elif analysis["combined_score"] > 0.4:
        analysis["recommendation"] = "🟡 Moderate conditions - Review carefully before proceeding"
    else:
        analysis["recommendation"] = "🔴 Poor conditions - Consider delaying or alternative options"
    
    return analysis

# Health and monitoring endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    services_status = {}
    
    # Check each MCP service
    for client, name in [(weather_client, "weather"), (market_client, "market"), (transport_client, "transport")]:
        try:
            # Simple health check - try to connect
            response = await client.http_client.get(f"{client.base_url}/health", timeout=3.0)
            services_status[name] = "healthy" if response.status_code == 200 else "degraded"
        except:
            services_status[name] = "unavailable"
    
    overall_status = "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MCP Brain API",
        "version": "2.0.0",
        "services": services_status
    }

@app.get("/metrics")
async def get_metrics(current_user: User = Depends(get_current_active_user)):
    """Get system metrics"""
    return {
        "rate_limiter": {
            "active_clients": len(rate_limiter.requests),
            "total_requests": sum(len(reqs) for reqs in rate_limiter.requests.values())
        },
        "circuit_breakers": {
            "weather": {
                "open": weather_client.circuit_open,
                "failures": weather_client.failure_count
            },
            "market": {
                "open": market_client.circuit_open,
                "failures": market_client.failure_count
            },
            "transport": {
                "open": transport_client.circuit_open,
                "failures": transport_client.failure_count
            }
        }
    }

# Service status endpoint
@app.get("/status")
async def service_status():
    """Check status of all MCP services"""
    services = {
        "weather": "http://localhost:8001",
        "market": "http://localhost:8002", 
        "transport": "http://localhost:8003"
    }
    
    status_results = {}
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=3)
            status_results[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException:
            status_results[service_name] = {
                "status": "unreachable",
                "response_time": None
            }
    
    return {
        "brain_service": "healthy",
        "mcp_services": status_results,
        "timestamp": datetime.utcnow().isoformat()
    }

# Protected admin endpoint
@app.get("/admin/stats")
async def get_admin_stats(current_user: User = Depends(get_current_active_user)):
    # Check admin role
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return {
        "users": len(fake_users_db),
        "active_services": 3,
        "service_ports": {
            "weather": 8001,
            "market": 8002,
            "transport": 8003,
            "brain": 8000
        },
        "last_updated": datetime.utcnow().isoformat(),
        "admin_user": current_user.username
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP Brain API Server v2.0",
        "description": "Intelligent farm-to-market orchestration",
        "version": "2.0.0",
        "features": [
            "Multi-service MCP integration",
            "Intelligent analysis and recommendations",
            "Circuit breaker pattern",
            "Rate limiting",
            "Response caching",
            "Comprehensive monitoring"
        ],
        "endpoints": {
            "auth": "POST /token",
            "query": "POST /query",
            "health": "GET /health",
            "metrics": "GET /metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)