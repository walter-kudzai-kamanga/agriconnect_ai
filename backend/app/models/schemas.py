from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class CropType(str, Enum):
    TOMATOES = "tomatoes"
    MAIZE = "maize"
    BEANS = "beans"
    POTATOES = "potatoes"
    CABBAGE = "cabbage"
    OTHER = "other"

class VehicleType(str, Enum):
    TRUCK = "truck"
    VAN = "van"
    PICKUP = "pickup"
    MOTORCYCLE = "motorcycle"

class JobStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class HealthCheck(BaseModel):
    status: str
    message: str

class FarmerRequest(BaseModel):
    crop_type: CropType
    quantity_kg: float = Field(..., gt=0)
    location: str
    destination_market: str
    preferred_delivery_time: Optional[str] = None

class TransporterProfile(BaseModel):
    vehicle_type: VehicleType
    capacity_kg: float
    current_location: str
    availability: bool = True
    contact_info: str

class TransportJob(BaseModel):
    id: Optional[int] = None
    farmer_request: FarmerRequest
    transporter: Optional[TransporterProfile] = None
    status: JobStatus = JobStatus.PENDING
    estimated_arrival: Optional[str] = None
    route_optimization: Optional[Dict] = None
    spoilage_risk: Optional[float] = None
    created_at: Optional[datetime] = None

class RouteOptimization(BaseModel):
    optimal_route: List[str]
    estimated_duration_minutes: int
    distance_km: float
    weather_conditions: Optional[Dict] = None
    road_conditions: Optional[str] = None

class MarketData(BaseModel):
    market_name: str
    commodity_prices: Dict[str, float]
    demand_level: str  # high, medium, low
    location: str