from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


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


# USSD Models
class USSDSession(BaseModel):
    phone_number: str
    stage: str
    data: Dict
    created_at: datetime
    last_activity: datetime

class TransportRequest(BaseModel):
    product: str
    quantity: int
    start_location: str
    destination: str
    farmer_phone: str

class RouteOptimization(BaseModel):
    route: str
    estimated_time: str
    distance: str
    cost_estimate: float
    spoilage_risk: float
    recommendations: List[str]

# SMS Models
class SMSRequest(BaseModel):
    from_number: str
    text: str
    timestamp: Optional[datetime] = None

class SMSResponse(BaseModel):
    to_number: str
    message: str
    status: str = "success"

class SMSProductRequest(BaseModel):
    product: str
    quantity: float
    start_location: str
    destination: str
    farmer_phone: str

# Shared Data Models
class Transporter(BaseModel):
    id: str
    name: str
    type: str
    capacity: int
    cost_per_km: float
    rating: float
    phone: str
    specialties: List[str]

class WeatherData(BaseModel):
    temperature: float
    condition: str
    humidity: int
    wind_speed: int
    rain_probability: int

class MarketPriceData(BaseModel):
    product: str
    prices: Dict[str, float]
    highest: float
    lowest: float
    average: float