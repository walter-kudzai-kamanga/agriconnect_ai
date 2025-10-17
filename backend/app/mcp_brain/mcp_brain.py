import os
import requests
import math
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration (move to .env in production)
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User model (in production, use a database)
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[str] = ["user"]  # Default role

# Mock user database (replace with real DB in production)
fake_users_db = {
    "walter": {
        "username": "walter",
        "full_name": "Walter Test User",
        "email": "walter@example.com",
        "hashed_password": "walehashed",  # Password is "wale"
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

# MCP Server Clients
class MCPServiceClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.session = requests.Session()
        
    def query(self, endpoint: str, data: dict, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self.session.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying {self.service_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{self.service_name} service is currently unavailable"
            )

# Initialize MCP service clients
weather_client = MCPServiceClient("http://localhost:8001", "weather")
market_client = MCPServiceClient("http://localhost:8002", "market")
transport_client = MCPServiceClient("http://localhost:8003", "transport")

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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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

def role_required(required_roles: list):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            if not any(role in current_user.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# FastAPI app
app = FastAPI(title="MCP Brain API", version="1.0.0")

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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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

# MCP Query Endpoint with Authentication and Authorization
@app.post("/query")
@role_required(["user"])  # Only users with 'user' role can access
async def query_mcp_contexts(
    lat: float,
    lon: float,
    product: str,
    capacity: float,
    location: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Query multiple MCP services with authentication and authorization.
    """
    try:
        # Get auth token for downstream services
        token = create_access_token(
            data={"sub": current_user.username, "roles": current_user.roles}
        )
        
        # Query services in parallel
        weather = weather_client.query("query", {"lat": lat, "lon": lon}, token)
        market = market_client.query("query", {"product": product}, token)
        transport = transport_client.query("query", {
            "farmer_location": location, 
            "required_capacity_kg": capacity
        }, token)

        # Contextual Reasoning Logic
        # 1. Weather Influence
        weather_description = weather.get("data", {}).get("condition", "").lower()
        good_weather = weather_description not in ["rain", "storm", "flood", "heavy rain"]
        weather_score = 1.0 if good_weather else 0.5

        # 2. Market Ranking (price and distance)
        markets = market.get("data", {}).get("markets", [])
        price_scores = []
        for m in markets:
            price = m.get("price_local", 0)
            if price > 0:  # Avoid division by zero
                price_scores.append(price)
        
        market_scores = []
        for m in markets:
            price = m.get("price_local", 0)
            if not price_scores:  # If no valid prices
                score = 0
            else:
                score = min(price / max(price_scores), 1.0) if max(price_scores) > 0 else 0
            market_scores.append({**m, "score": score})

        # 3. Transport Availability
        transport_available = bool(transport.get("data", {}).get("available_trucks"))
        transport_score = 1.0 if transport_available else 0.2

        # Combine scores (simple average for now)
        combined_score = (weather_score + 
                         (sum(m["score"] for m in market_scores) / len(market_scores) if market_scores else 0) + 
                         transport_score) / 3

        # Generate recommendation
        if combined_score > 0.8:
            recommendation = "Excellent conditions - Proceed immediately"
        elif combined_score > 0.6:
            recommendation = "Good conditions - Proceed"
        elif combined_score > 0.4:
            recommendation = "Moderate conditions - Review recommended"
        else:
            recommendation = "Poor conditions - Delay or find alternatives"

        return {
            "status": "success",
            "user": current_user.username,
            "data": {
                "weather": weather,
                "market": market,
                "transport": transport,
                "analysis": {
                    "weather_score": weather_score,
                    "market_score": market_scores[0]["score"] if market_scores else 0,
                    "transport_score": transport_score,
                    "combined_score": round(combined_score, 2)
                },
                "recommendation": recommendation
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "services_queried": ["weather", "market", "transport"]
            }
        }

    except Exception as e:
        logger.error(f"Error in MCP query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process MCP query"
        )

# Simple query endpoint for quick testing
@app.post("/query/simple")
@role_required(["user"])
async def simple_query(
    product: str,
    lat: float = -17.825,
    lon: float = 31.030,
    current_user: User = Depends(get_current_active_user)
):
    """Simplified query for quick testing"""
    location = {"lat": lat, "lon": lon}
    return await query_mcp_contexts(lat, lon, product, 500.0, location, current_user)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MCP Brain API",
        "version": "1.0.0"
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
@role_required(["admin"])  # Only admins can access
async def get_admin_stats(current_user: User = Depends(get_current_active_user)):
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
        "message": "MCP Brain API Server",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "login": "POST /token",
                "current_user": "GET /users/me/"
            },
            "queries": {
                "full_query": "POST /query",
                "simple_query": "POST /query/simple"
            },
            "info": {
                "health": "GET /health",
                "status": "GET /status",
                "test_users": "GET /test-users"
            },
            "admin": {
                "stats": "GET /admin/stats (admin role required)"
            }
        },
        "test_credentials": {
            "username": "walter",
            "password": "wale",
            "roles": ["user", "admin"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)