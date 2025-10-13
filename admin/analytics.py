from typing import Dict, List
from datetime import datetime, timedelta
import numpy as np

class AdminAnalytics:
    """Analytics engine for admin dashboard"""
    
    def __init__(self):
        self.regions = [
            "Mashonaland East", "Mashonaland Central", "Masvingo", 
            "Manicaland", "Matabeleland North", "Matabeleland South",
            "Midlands", "Harare", "Bulawayo"
        ]
    
    def calculate_growth_metrics(self, period_days: int = 30) -> Dict:
        """Calculate growth metrics for the platform"""
        # Mock growth data
        base_users = 150
        base_jobs = 300
        base_produce = 45000  # kg
        
        growth_rate = 0.15  # 15% monthly growth
        
        current_users = int(base_users * (1 + growth_rate))
        current_jobs = int(base_jobs * (1 + growth_rate))
        current_produce = int(base_produce * (1 + growth_rate))
        
        return {
            "user_growth": {
                "current": current_users,
                "previous": base_users,
                "growth_percentage": growth_rate * 100
            },
            "job_growth": {
                "current": current_jobs,
                "previous": base_jobs,
                "growth_percentage": growth_rate * 100
            },
            "produce_growth": {
                "current_kg": current_produce,
                "previous_kg": base_produce,
                "growth_percentage": growth_rate * 100
            }
        }
    
    def predict_demand(self, days: int = 7) -> Dict:
        """Predict demand for the next few days"""
        # Mock demand prediction based on historical patterns
        predictions = []
        current_date = datetime.now()
        
        for i in range(days):
            date = current_date + timedelta(days=i)
            # Mock seasonal variation
            seasonal_factor = 1.0 + 0.1 * np.sin(i * 2 * np.pi / 7)  # Weekly pattern
            base_demand = 50  # base jobs per day
            
            predicted_jobs = int(base_demand * seasonal_factor)
            predicted_produce = predicted_jobs * 350  # avg 350kg per job
            
            predictions.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_jobs": predicted_jobs,
                "predicted_produce_kg": predicted_produce,
                "confidence": 0.85 - (i * 0.05)  # Decreasing confidence for future days
            })
        
        return {"predictions": predictions}
    
    def calculate_economic_impact(self) -> Dict:
        """Calculate estimated economic impact"""
        # Mock economic impact calculations
        avg_farmer_income_increase = 350  # USD per farmer per month
        avg_transporter_income = 1200     # USD per transporter per month
        spoilage_cost_saved = 2.5         # USD per kg spoilage prevented
        
        total_farmers = 150
        total_transporters = 45
        total_spoilage_prevented = 12500  # kg
        
        return {
            "farmer_income_generated": total_farmers * avg_farmer_income_increase,
            "transporter_income_generated": total_transporters * avg_transporter_income,
            "spoilage_cost_saved": total_spoilage_prevented * spoilage_cost_saved,
            "total_economic_impact": (
                total_farmers * avg_farmer_income_increase +
                total_transporters * avg_transporter_income +
                total_spoilage_prevented * spoilage_cost_saved
            ),
            "currency": "USD"
        }