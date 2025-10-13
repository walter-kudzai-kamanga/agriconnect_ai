from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta
from app.models.schemas import TransportJob, FarmerRequest, TransporterProfile

router = APIRouter()

# Mock data for demonstration
MOCK_JOBS = [
    TransportJob(
        id=1,
        farmer_request=FarmerRequest(
            crop_type="tomatoes",
            quantity_kg=500,
            location="Mashonaland East",
            destination_market="Mbare Musika"
        ),
        transporter=TransporterProfile(
            vehicle_type="truck",
            capacity_kg=2000,
            current_location="Harare",
            availability=True,
            contact_info="+263771234567"
        ),
        status="completed",
        estimated_arrival=(datetime.now() - timedelta(hours=2)).isoformat(),
        spoilage_risk=0.15,
        created_at=(datetime.now() - timedelta(days=1)).isoformat()
    ),
    TransportJob(
        id=2,
        farmer_request=FarmerRequest(
            crop_type="maize",
            quantity_kg=1000,
            location="Mashonaland Central",
            destination_market="Sakubva Market"
        ),
        transporter=TransporterProfile(
            vehicle_type="van",
            capacity_kg=800,
            current_location="Chitungwiza",
            availability=True,
            contact_info="+263772345678"
        ),
        status="in_progress",
        estimated_arrival=(datetime.now() + timedelta(hours=1)).isoformat(),
        spoilage_risk=0.08,
        created_at=datetime.now().isoformat()
    )
]

MOCK_USERS = {
    "farmers": [
        {"id": 1, "name": "John Moyo", "location": "Mashonaland East", "join_date": "2024-01-15", "completed_jobs": 12},
        {"id": 2, "name": "Sarah Ndlovu", "location": "Mashonaland Central", "join_date": "2024-02-20", "completed_jobs": 8},
        {"id": 3, "name": "David Chiweshe", "location": "Masvingo", "join_date": "2024-03-10", "completed_jobs": 5}
    ],
    "transporters": [
        {"id": 1, "name": "Tinashe Transport", "vehicle_type": "truck", "capacity_kg": 2000, "rating": 4.5, "completed_jobs": 45},
        {"id": 2, "name": "Blessing Deliveries", "vehicle_type": "van", "capacity_kg": 800, "rating": 4.2, "completed_jobs": 32},
        {"id": 3, "name": "Chido Couriers", "vehicle_type": "pickup", "capacity_kg": 500, "rating": 4.7, "completed_jobs": 28}
    ]
}

@router.get("/dashboard-stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        total_jobs = len(MOCK_JOBS)
        completed_jobs = len([job for job in MOCK_JOBS if job.status == "completed"])
        in_progress_jobs = len([job for job in MOCK_JOBS if job.status == "in_progress"])
        pending_jobs = len([job for job in MOCK_JOBS if job.status == "pending"])
        
        total_farmers = len(MOCK_USERS["farmers"])
        total_transporters = len(MOCK_USERS["transporters"])
        
        # Calculate total produce transported
        total_produce_kg = sum(
            job.farmer_request.quantity_kg 
            for job in MOCK_JOBS 
            if job.status == "completed"
        )
        
        # Calculate estimated spoilage prevented
        spoilage_prevented = sum(
            job.farmer_request.quantity_kg * (job.spoilage_risk or 0)
            for job in MOCK_JOBS
            if job.status == "completed"
        )
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "in_progress_jobs": in_progress_jobs,
            "pending_jobs": pending_jobs,
            "total_farmers": total_farmers,
            "total_transporters": total_transporters,
            "total_produce_kg": total_produce_kg,
            "spoilage_prevented_kg": spoilage_prevented,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-jobs")
async def get_recent_jobs(limit: int = 10):
    """Get recent transport jobs"""
    try:
        recent_jobs = MOCK_JOBS[:limit]
        return {"jobs": recent_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_users(user_type: str = None):
    """Get users (farmers or transporters)"""
    try:
        if user_type == "farmers":
            return {"users": MOCK_USERS["farmers"]}
        elif user_type == "transporters":
            return {"users": MOCK_USERS["transporters"]}
        else:
            return MOCK_USERS
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/regional-stats")
async def get_regional_stats():
    """Get regional statistics"""
    try:
        regional_data = {
            "regions": [
                {
                    "name": "Mashonaland East",
                    "jobs_completed": 45,
                    "produce_kg": 12500,
                    "farmers_count": 23,
                    "transporters_count": 8
                },
                {
                    "name": "Mashonaland Central",
                    "jobs_completed": 32,
                    "produce_kg": 8900,
                    "farmers_count": 18,
                    "transporters_count": 6
                },
                {
                    "name": "Masvingo",
                    "jobs_completed": 28,
                    "produce_kg": 7600,
                    "farmers_count": 15,
                    "transporters_count": 5
                },
                {
                    "name": "Manicaland",
                    "jobs_completed": 21,
                    "produce_kg": 5400,
                    "farmers_count": 12,
                    "transporters_count": 4
                }
            ]
        }
        return regional_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/crop-stats")
async def get_crop_statistics():
    """Get crop-wise statistics"""
    try:
        crop_data = {
            "crops": [
                {"name": "Tomatoes", "volume_kg": 8500, "jobs_count": 34, "avg_spoilage_risk": 0.18},
                {"name": "Maize", "volume_kg": 12000, "jobs_count": 28, "avg_spoilage_risk": 0.08},
                {"name": "Beans", "volume_kg": 4200, "jobs_count": 15, "avg_spoilage_risk": 0.12},
                {"name": "Potatoes", "volume_kg": 6800, "jobs_count": 22, "avg_spoilage_risk": 0.15},
                {"name": "Cabbage", "volume_kg": 3100, "jobs_count": 12, "avg_spoilage_risk": 0.25}
            ]
        }
        return crop_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/performance")
async def get_performance_metrics(days: int = 30):
    """Get performance metrics over time"""
    try:
        # Generate mock time series data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        dates = []
        jobs_completed = []
        produce_transported = []
        spoilage_prevented = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y-%m-%d"))
            # Mock data with some variation
            jobs_completed.append(max(1, int(10 + (current_date.day % 10))))
            produce_transported.append(max(100, int(500 + (current_date.day % 20) * 100)))
            spoilage_prevented.append(max(10, int(50 + (current_date.day % 15) * 10)))
            current_date += timedelta(days=1)
        
        return {
            "dates": dates,
            "jobs_completed": jobs_completed,
            "produce_transported_kg": produce_transported,
            "spoilage_prevented_kg": spoilage_prevented
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast-notification")
async def broadcast_notification(notification: Dict):
    """Broadcast notification to users"""
    try:
        # In production, this would integrate with push notification services
        return {
            "success": True,
            "message": f"Notification sent to {notification.get('target', 'all')} users",
            "notification": notification
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-health")
async def get_system_health():
    """Get system health status"""
    try:
        return {
            "status": "healthy",
            "api_uptime": "99.8%",
            "database_status": "connected",
            "active_connections": 42,
            "response_time_ms": 45,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))