from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    FarmerRequest, TransportJob, RouteOptimization, 
    MarketData, TransporterProfile
)
from .spoilage_model import SpoilagePredictor
from app.tracking.gps_tracker import gps_tracker
from app.ml.price_forecaster import price_forecaster
from app.offline.offline_storage import OfflineStorage
from app.i18n.translations import translator
from typing import List, Dict, Optional
import random
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()
spoilage_predictor = SpoilagePredictor()
offline_storage = OfflineStorage()

# New request models
class GPSUpdateRequest(BaseModel):
    job_id: str
    lat: float
    lon: float
    speed: Optional[float] = None
    heading: Optional[float] = None

class PriceForecastRequest(BaseModel):
    product: str
    market: str
    days: int = 7

class LanguageRequest(BaseModel):
    language: str  # 'en', 'sn', 'nd'

# Mock data for demonstration
MOCK_TRANSPORTERS = [
    TransporterProfile(
        vehicle_type="truck",
        capacity_kg=2000,
        current_location="Harare",
        availability=True,
        contact_info="+263771234567"
    ),
    TransporterProfile(
        vehicle_type="van",
        capacity_kg=800,
        current_location="Chitungwiza",
        availability=True,
        contact_info="+263772345678"
    ),
    TransporterProfile(
        vehicle_type="pickup",
        capacity_kg=500,
        current_location="Epworth",
        availability=True,
        contact_info="+263773456789"
    )
]

MOCK_MARKETS = {
    "Mbare Musika": MarketData(
        market_name="Mbare Musika",
        commodity_prices={"tomatoes": 2.5, "maize": 1.8, "beans": 3.2},
        demand_level="high",
        location="Harare"
    ),
    "Sakubva": MarketData(
        market_name="Sakubva",
        commodity_prices={"tomatoes": 2.3, "maize": 1.7, "beans": 3.0},
        demand_level="medium",
        location="Mutare"
    )
}

@router.post("/match-transport")
async def match_transport_request(farmer_request: FarmerRequest):
    """
    Match farmer request with available transporters
    """
    try:
        # Filter available transporters with sufficient capacity
        suitable_transporters = [
            t for t in MOCK_TRANSPORTERS 
            if t.availability and t.capacity_kg >= farmer_request.quantity_kg
        ]
        
        if not suitable_transporters:
            raise HTTPException(status_code=404, detail="No available transporters found")
        
        # Select best match (closest location, optimal vehicle type)
        selected_transporter = suitable_transporters[0]
        
        # Generate route optimization
        route_data = await optimize_route(
            farmer_request.location, 
            farmer_request.destination_market
        )
        
        # Predict spoilage risk
        spoilage_risk = spoilage_predictor.predict_risk(
            crop_type=farmer_request.crop_type,
            estimated_duration=route_data.estimated_duration_minutes,
            weather_conditions=route_data.weather_conditions
        )
        
        # Create transport job
        transport_job = TransportJob(
            farmer_request=farmer_request,
            transporter=selected_transporter,
            status="matched",
            estimated_arrival=(
                datetime.now() + 
                timedelta(minutes=route_data.estimated_duration_minutes)
            ).isoformat(),
            route_optimization=route_data.dict(),
            spoilage_risk=spoilage_risk,
            created_at=datetime.now()
        )
        
        return {
            "success": True,
            "transport_job": transport_job,
            "message": f"Matched with {selected_transporter.vehicle_type} transporter"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-route")
async def optimize_route(start_location: str, end_location: str):
    """
    Optimize delivery route considering multiple factors
    """
    try:
        # Mock route optimization - in production, integrate with Google Maps/OSRM
        optimal_route = [start_location, "Intermediate Point", end_location]
        
        # Mock weather and road conditions
        weather_conditions = {
            "temperature": 25 + random.randint(-5, 5),
            "humidity": 60 + random.randint(-20, 20),
            "rain_probability": random.randint(0, 100)
        }
        
        route_data = RouteOptimization(
            optimal_route=optimal_route,
            estimated_duration_minutes=120 + random.randint(-30, 60),
            distance_km=45 + random.randint(-15, 30),
            weather_conditions=weather_conditions,
            road_conditions="good" if random.random() > 0.3 else "moderate"
        )
        
        return route_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{market_name}")
async def get_market_data(market_name: str):
    """
    Get current market data and prices
    """
    market = MOCK_MARKETS.get(market_name)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    return market

@router.get("/available-transporters")
async def get_available_transporters():
    """
    Get list of all available transporters
    """
    available = [t for t in MOCK_TRANSPORTERS if t.availability]
    return {"available_transporters": available}

@router.post("/predict-spoilage")
async def predict_spoilage_risk(
    crop_type: str, 
    estimated_duration: int, 
    temperature: float
):
    """
    Predict spoilage risk for a given crop and conditions
    """
    try:
        risk_score = spoilage_predictor.predict_risk(
            crop_type=crop_type,
            estimated_duration=estimated_duration,
            weather_conditions={"temperature": temperature}
        )
        
        return {
            "crop_type": crop_type,
            "estimated_duration_minutes": estimated_duration,
            "temperature_celsius": temperature,
            "spoilage_risk_percentage": risk_score * 100,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoints for enhanced features

@router.post("/tracking/start")
async def start_tracking(
    job_id: str,
    transporter_phone: str,
    farmer_phone: str,
    route_info: Dict
):
    """Start GPS tracking for a transport job"""
    try:
        result = gps_tracker.start_tracking(job_id, transporter_phone, farmer_phone, route_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tracking/update")
async def update_gps_location(request: GPSUpdateRequest):
    """Update GPS location for a tracked job"""
    try:
        result = gps_tracker.update_location(
            request.job_id,
            request.lat,
            request.lon,
            request.speed,
            request.heading
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracking/status/{job_id}")
async def get_tracking_status(job_id: str):
    """Get current tracking status for a job"""
    try:
        status = gps_tracker.get_tracking_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Tracking not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracking/active")
async def get_all_active_trackings():
    """Get all active tracking jobs"""
    try:
        return gps_tracker.get_all_active_trackings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast/price")
async def forecast_price(request: PriceForecastRequest):
    """Get price forecast for a product"""
    try:
        forecast = price_forecaster.forecast(
            request.product,
            request.market,
            request.days
        )
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offline/stats")
async def get_offline_stats():
    """Get offline storage statistics"""
    try:
        return offline_storage.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offline/pending")
async def get_pending_requests(limit: int = 50):
    """Get pending offline requests"""
    try:
        return offline_storage.get_pending_requests(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/i18n/translate")
async def translate_text(key: str, lang: str = "en"):
    """Get translation for a key"""
    try:
        return {
            "key": key,
            "language": lang,
            "translation": translator.translate(key, lang)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))