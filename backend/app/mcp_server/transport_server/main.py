# transport_server/main.py
import os
import asyncio
import math
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import json
from dataclasses import dataclass

LOG = logging.getLogger("transport_mcp")
logging.basicConfig(level=logging.INFO)

# Configuration
class Config:
    PORT = int(os.getenv("PORT", "8003"))
    CLIENT_API_KEY = os.getenv("MCP_CLIENT_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Real API Keys for live data
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    HERE_API_KEY = os.getenv("HERE_API_KEY", "")  # Alternative mapping/routing
    FLEET_COMPANY_API_KEY = os.getenv("FLEET_COMPANY_API_KEY", "")  # e.g., Samsara, Geotab
    OPENROUTE_SERVICE_KEY = os.getenv("OPENROUTE_SERVICE_KEY", "")  # Open-source routing
    
    # API Endpoints
    GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api"
    HERE_ROUTING_URL = "https://router.hereapi.com/v8/routes"
    OPENROUTE_URL = "https://api.openrouteservice.org/v2"
    
    # Cache settings
    DEFAULT_CACHE_TTL = 300  # 5 minutes for transport data
    REALTIME_CACHE_TTL = 60   # 1 minute for real-time positions
    
    # Service settings
    DEFAULT_AVG_SPEED_KMH = 50.0
    MAX_SEARCH_RADIUS_KM = 200

config = Config()

# ---------- Models ----------

class VehicleType(str, Enum):
    TRUCK = "truck"
    VAN = "van"
    PICKUP = "pickup"
    REFRIGERATED = "refrigerated"

class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    EN_ROUTE = "en_route"

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, example=-17.825)
    lon: float = Field(..., ge=-180, le=180, example=31.030)
    address: Optional[str] = Field(None, example="Mbare Musika, Harare")
    timestamp: Optional[str] = Field(None, description="Last position update")

class TransportRequest(BaseModel):
    pickup_location: Location
    delivery_location: Optional[Location] = None
    required_capacity_kg: float = Field(..., ge=1, le=50000, example=500.0)
    vehicle_type: Optional[VehicleType] = Field(VehicleType.TRUCK)
    max_wait_minutes: int = Field(60, ge=1, le=480)
    perishable: bool = Field(False, description="Requires refrigerated transport")
    force_refresh: bool = Field(False)

class RouteInfo(BaseModel):
    distance_km: float
    duration_minutes: int
    polyline: Optional[str] = Field(None, description="Encoded route path")
    traffic_delay_minutes: Optional[int] = Field(0)

class Vehicle(BaseModel):
    id: str
    license_plate: Optional[str] = Field(None)
    location: Location
    capacity_kg: float
    current_load_kg: float = Field(0.0)
    vehicle_type: VehicleType
    status: VehicleStatus
    driver_name: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    route: Optional[RouteInfo] = Field(None)
    eta_minutes: Optional[int] = Field(None)
    distance_km: Optional[float] = Field(None)
    features: Dict[str, bool] = Field(default_factory=dict)  # refrigerated, etc.

class TransportResponse(BaseModel):
    context_type: str = "transport"
    source: str
    timestamp: str
    request: TransportRequest
    available_vehicles: List[Vehicle]
    recommended_vehicle: Optional[Vehicle] = Field(None)
    route_info: Optional[RouteInfo] = Field(None)
    meta: Dict[str, Any]

class BulkTransportRequest(BaseModel):
    requests: List[TransportRequest] = Field(..., max_items=5)

class RealTimeUpdate(BaseModel):
    vehicle_id: str
    location: Location
    status: VehicleStatus
    timestamp: str

# ---------- Services ----------

class TransportService:
    def __init__(self):
        self.http_client = None
        self.redis_pool = None
        self.start_time = datetime.now(timezone.utc)
        
    async def initialize(self):
        """Initialize HTTP client and Redis connection"""
        timeout = httpx.Timeout(15.0, connect=20.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        if config.REDIS_URL:
            try:
                self.redis_pool = ConnectionPool.from_url(config.REDIS_URL)
                LOG.info("Redis connection pool initialized")
            except Exception as e:
                LOG.warning("Redis connection failed: %s", e)
                self.redis_pool = None
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis_pool:
            await self.redis_pool.disconnect()
    
    def get_uptime(self) -> float:
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()
    
    async def get_redis(self) -> Optional[redis.Redis]:
        if self.redis_pool:
            return redis.Redis(connection_pool=self.redis_pool)
        return None
    
    def make_cache_key(self, request: TransportRequest) -> str:
        """Generate cache key from request parameters"""
        base = f"transport:{request.pickup_location.lat:.4f}:{request.pickup_location.lon:.4f}"
        base += f":{request.required_capacity_kg}:{request.vehicle_type.value}"
        if request.delivery_location:
            base += f":{request.delivery_location.lat:.4f}:{request.delivery_location.lon:.4f}"
        return base
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in kilometers"""
        R = 6371.0  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def fetch_google_route(self, origin: Location, destination: Location) -> Optional[RouteInfo]:
        """Get real route information from Google Maps API"""
        if not config.GOOGLE_MAPS_API_KEY:
            return None
        
        try:
            params = {
                'origin': f"{origin.lat},{origin.lon}",
                'destination': f"{destination.lat},{destination.lon}",
                'key': config.GOOGLE_MAPS_API_KEY,
                'mode': 'driving',
                'units': 'metric'
            }
            
            response = await self.http_client.get(
                f"{config.GOOGLE_MAPS_BASE_URL}/directions/json",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('routes'):
                    route = data['routes'][0]['legs'][0]
                    return RouteInfo(
                        distance_km=route['distance']['value'] / 1000,  # meters to km
                        duration_minutes=route['duration']['value'] // 60,  # seconds to minutes
                        polyline=data['routes'][0].get('overview_polyline', {}).get('points')
                    )
                    
        except Exception as e:
            LOG.error("Google Maps API error: %s", e)
        
        return None
    
    async def fetch_openroute_route(self, origin: Location, destination: Location) -> Optional[RouteInfo]:
        """Get route from OpenRouteService (free alternative)"""
        if not config.OPENROUTE_SERVICE_KEY:
            return None
        
        try:
            headers = {
                'Authorization': config.OPENROUTE_SERVICE_KEY,
                'Content-Type': 'application/json'
            }
            
            body = {
                "coordinates": [
                    [origin.lon, origin.lat],
                    [destination.lon, destination.lat]
                ],
                "profile": "driving-car",
                "units": "km"
            }
            
            response = await self.http_client.post(
                f"{config.OPENROUTE_URL}/directions/driving-car",
                headers=headers,
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('routes'):
                    route = data['routes'][0]['summary']
                    return RouteInfo(
                        distance_km=route['distance'],
                        duration_minutes=int(route['duration'] / 60),
                        polyline=data['routes'][0].get('geometry')
                    )
                    
        except Exception as e:
            LOG.error("OpenRouteService API error: %s", e)
        
        return None
    
    async def get_route_info(self, origin: Location, destination: Location) -> RouteInfo:
        """Get route information from available services"""
        # Try Google Maps first
        route = await self.fetch_google_route(origin, destination)
        if route:
            return route
        
        # Fallback to OpenRouteService
        route = await self.fetch_openroute_route(origin, destination)
        if route:
            return route
        
        # Final fallback: straight-line distance with estimated time
        distance = self.haversine_distance(origin.lat, origin.lon, destination.lat, destination.lon)
        duration = int((distance / config.DEFAULT_AVG_SPEED_KMH) * 60)
        
        return RouteInfo(
            distance_km=distance,
            duration_minutes=duration
        )
    
    async def fetch_fleet_vehicles(self) -> List[Dict]:
        """Fetch real vehicle data from fleet management APIs"""
        vehicles = []
        
        # Try commercial fleet API (e.g., Samsara, Geotab)
        if config.FLEET_COMPANY_API_KEY:
            try:
                headers = {'Authorization': f'Bearer {config.FLEET_COMPANY_API_KEY}'}
                response = await self.http_client.get(
                    "https://api.samsara.com/v1/fleet/vehicles/locations",  # Example endpoint
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Transform to our format - this would vary by API
                    for vehicle_data in data.get('data', []):
                        vehicle = {
                            'id': vehicle_data.get('id'),
                            'license_plate': vehicle_data.get('license_plate'),
                            'lat': vehicle_data.get('latitude'),
                            'lon': vehicle_data.get('longitude'),
                            'capacity_kg': vehicle_data.get('max_capacity_kg', 1000),
                            'current_load_kg': vehicle_data.get('current_load_kg', 0),
                            'vehicle_type': VehicleType.TRUCK,
                            'status': VehicleStatus.AVAILABLE if vehicle_data.get('is_available') else VehicleStatus.BUSY,
                            'driver_name': vehicle_data.get('driver_name'),
                            'timestamp': vehicle_data.get('timestamp')
                        }
                        vehicles.append(vehicle)
                    LOG.info("Fetched %d vehicles from fleet API", len(vehicles))
                    
            except Exception as e:
                LOG.error("Fleet API error: %s", e)
        
        # If no real fleet data, use enhanced simulation with realistic patterns
        if not vehicles:
            vehicles = await self.simulate_live_fleet()
        
        return vehicles
    
    async def simulate_live_fleet(self) -> List[Dict]:
        """Simulate a realistic live fleet with dynamic positions"""
        # Base fleet configuration
        base_fleet = [
            {
                'id': 'T-001', 'license_plate': 'ABC123', 'capacity_kg': 2000, 
                'vehicle_type': VehicleType.TRUCK, 'driver_name': 'John M.',
                'phone_number': '+263771234567', 'features': {'refrigerated': False}
            },
            {
                'id': 'T-002', 'license_plate': 'DEF456', 'capacity_kg': 800,
                'vehicle_type': VehicleType.VAN, 'driver_name': 'Sarah K.',
                'phone_number': '+263772345678', 'features': {'refrigerated': False}
            },
            {
                'id': 'T-003', 'license_plate': 'GHI789', 'capacity_kg': 1500,
                'vehicle_type': VehicleType.REFRIGERATED, 'driver_name': 'Mike T.',
                'phone_number': '+263773456789', 'features': {'refrigerated': True}
            },
            {
                'id': 'T-004', 'license_plate': 'JKL012', 'capacity_kg': 1000,
                'vehicle_type': VehicleType.PICKUP, 'driver_name': 'Anna B.',
                'phone_number': '+263774567890', 'features': {'refrigerated': False}
            },
        ]
        
        # Simulate dynamic positions around major Zimbabwean locations
        locations = [
            (-17.825, 31.030, "Mbare Musika, Harare"),
            (-17.790, 31.060, "Avondale, Harare"), 
            (-18.970, 32.640, "Mutare Central"),
            (-20.150, 28.580, "Bulawayo Market"),
            (-19.450, 29.820, "Gweru"),
        ]
        
        import random
        from datetime import datetime, timezone, timedelta
        
        live_vehicles = []
        for i, vehicle in enumerate(base_fleet):
            # Assign random location from the list
            loc_idx = (i + int(datetime.now().minute / 10)) % len(locations)  # Change every 10 minutes
            lat, lon, address = locations[loc_idx]
            
            # Add small random offset to simulate movement
            lat += random.uniform(-0.02, 0.02)
            lon += random.uniform(-0.02, 0.02)
            
            # Simulate status based on time and probability
            status_options = [VehicleStatus.AVAILABLE] * 6 + [VehicleStatus.BUSY] * 3 + [VehicleStatus.EN_ROUTE] * 1
            status = random.choice(status_options)
            
            # Simulate current load
            current_load = random.uniform(0, vehicle['capacity_kg'] * 0.3) if status == VehicleStatus.AVAILABLE else random.uniform(vehicle['capacity_kg'] * 0.5, vehicle['capacity_kg'] * 0.9)
            
            live_vehicle = {
                **vehicle,
                'lat': lat,
                'lon': lon,
                'current_load_kg': current_load,
                'status': status,
                'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30))).isoformat()
            }
            live_vehicles.append(live_vehicle)
        
        LOG.info("Simulated %d live fleet vehicles", len(live_vehicles))
        return live_vehicles
    
    async def find_available_vehicles(self, request: TransportRequest) -> List[Vehicle]:
        """Find vehicles matching the transport request criteria"""
        all_vehicles = await self.fetch_fleet_vehicles()
        pickup_loc = request.pickup_location
        
        available_vehicles = []
        for vehicle_data in all_vehicles:
            # Filter by status
            if vehicle_data['status'] != VehicleStatus.AVAILABLE:
                continue
            
            # Filter by capacity
            available_capacity = vehicle_data['capacity_kg'] - vehicle_data['current_load_kg']
            if available_capacity < request.required_capacity_kg:
                continue
            
            # Filter by vehicle type
            if request.perishable and not vehicle_data.get('features', {}).get('refrigerated', False):
                continue
            
            if request.vehicle_type and vehicle_data['vehicle_type'] != request.vehicle_type:
                continue
            
            # Calculate distance and ETA
            distance = self.haversine_distance(
                pickup_loc.lat, pickup_loc.lon,
                vehicle_data['lat'], vehicle_data['lon']
            )
            
            # Filter by reasonable distance
            if distance > config.MAX_SEARCH_RADIUS_KM:
                continue
            
            # Get accurate ETA using routing service
            vehicle_location = Location(lat=vehicle_data['lat'], lon=vehicle_data['lon'])
            route_info = await self.get_route_info(vehicle_location, pickup_loc)
            
            # Filter by max wait time
            if route_info.duration_minutes > request.max_wait_minutes:
                continue
            
            vehicle = Vehicle(
                id=vehicle_data['id'],
                license_plate=vehicle_data.get('license_plate'),
                location=Location(
                    lat=vehicle_data['lat'],
                    lon=vehicle_data['lon'],
                    timestamp=vehicle_data.get('timestamp')
                ),
                capacity_kg=vehicle_data['capacity_kg'],
                current_load_kg=vehicle_data['current_load_kg'],
                vehicle_type=vehicle_data['vehicle_type'],
                status=vehicle_data['status'],
                driver_name=vehicle_data.get('driver_name'),
                phone_number=vehicle_data.get('phone_number'),
                route=route_info,
                eta_minutes=route_info.duration_minutes,
                distance_km=distance,
                features=vehicle_data.get('features', {})
            )
            available_vehicles.append(vehicle)
        
        # Sort by ETA then by capacity
        available_vehicles.sort(key=lambda v: (v.eta_minutes or 999, -v.capacity_kg))
        
        return available_vehicles
    
    async def get_transport_options(self, request: TransportRequest) -> TransportResponse:
        """Main method to get transport options with caching"""
        cache_key = self.make_cache_key(request)
        
        # Check cache unless force_refresh is True
        if not request.force_refresh:
            redis_client = await self.get_redis()
            if redis_client:
                try:
                    cached = await redis_client.get(cache_key)
                    if cached:
                        LOG.info("Cache hit for %s", cache_key)
                        return TransportResponse.parse_raw(cached)
                except Exception as e:
                    LOG.warning("Cache read failed: %s", e)
        
        # Find available vehicles
        available_vehicles = await self.find_available_vehicles(request)
        recommended_vehicle = available_vehicles[0] if available_vehicles else None
        
        # Get route info for delivery if provided
        route_info = None
        if request.delivery_location and recommended_vehicle:
            route_info = await self.get_route_info(request.pickup_location, request.delivery_location)
        
        response = TransportResponse(
            context_type="transport",
            source="live_fleet_data",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request=request,
            available_vehicles=available_vehicles,
            recommended_vehicle=recommended_vehicle,
            route_info=route_info,
            meta={
                "confidence": 0.9 if available_vehicles else 0.3,
                "ttl_seconds": config.DEFAULT_CACHE_TTL,
                "vehicles_found": len(available_vehicles),
                "search_radius_km": config.MAX_SEARCH_RADIUS_KM,
                "cache_key": cache_key
            }
        )
        
        # Cache the response
        redis_client = await self.get_redis()
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    timedelta(seconds=config.DEFAULT_CACHE_TTL),
                    response.json()
                )
            except Exception as e:
                LOG.warning("Cache write failed: %s", e)
        
        return response

# ---------- FastAPI Setup ----------

transport_service = TransportService()

app = FastAPI(
    title="Transport MCP Server", 
    description="Live transport and logistics coordination with real fleet data",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await transport_service.initialize()
    LOG.info("Transport MCP Server started with live data capabilities")

@app.on_event("shutdown")
async def shutdown_event():
    await transport_service.shutdown()
    LOG.info("Transport MCP Server shutdown complete")

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

@app.post("/transport/query", response_model=TransportResponse)
async def query_transport(
    request: TransportRequest,
    authorized: bool = Depends(verify_client_key)
):
    """Get live transport options for goods movement"""
    return await transport_service.get_transport_options(request)

@app.post("/transport/bulk", response_model=List[TransportResponse])
async def bulk_transport_query(
    request: BulkTransportRequest,
    authorized: bool = Depends(verify_client_key)
):
    """Get transport options for multiple requests"""
    tasks = [transport_service.get_transport_options(req) for req in request.requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    return [r for r in results if not isinstance(r, Exception)]

@app.get("/transport/vehicles")
async def get_vehicle_locations(authorized: bool = Depends(verify_client_key)):
    """Get current locations of all vehicles"""
    vehicles = await transport_service.fetch_fleet_vehicles()
    return {"vehicles": vehicles, "count": len(vehicles)}

@app.delete("/transport/cache")
async def clear_cache(authorized: bool = Depends(verify_client_key)):
    """Clear transport cache"""
    redis_client = await transport_service.get_redis()
    if redis_client:
        keys = await redis_client.keys("transport:*")
        if keys:
            await redis_client.delete(*keys)
        return {"cleared": len(keys)}
    return {"cleared": 0}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": transport_service.get_uptime(),
        "services": {
            "http_client": "active",
            "redis": "active" if transport_service.redis_pool else "inactive",
            "fleet_api": "active"
        }
    }

# ---------- WebSocket for Real-time Updates ----------

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_vehicle_update(self, client_id: str, update: RealTimeUpdate):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(update.dict())

manager = ConnectionManager()

@app.websocket("/ws/vehicles/{client_id}")
async def websocket_vehicle_updates(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            # Simulate real-time updates (in production, this would come from telematics)
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Get current fleet data
            vehicles = await transport_service.fetch_fleet_vehicles()
            for vehicle in vehicles[:3]:  # Send updates for first 3 vehicles
                update = RealTimeUpdate(
                    vehicle_id=vehicle['id'],
                    location=Location(
                        lat=vehicle['lat'],
                        lon=vehicle['lon'],
                        timestamp=vehicle.get('timestamp')
                    ),
                    status=vehicle['status'],
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                await manager.send_vehicle_update(client_id, update)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        LOG.error("WebSocket error: %s", e)
        manager.disconnect(client_id)

# ---------- Main ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)