import numpy as np
from typing import Dict

class SpoilagePredictor:
    """
    Predictive model for crop spoilage risk during transport
    """
    
    def __init__(self):
        # Base spoilage rates per crop type (per hour at 25°C)
        self.base_spoilage_rates = {
            "tomatoes": 0.02,  # 2% per hour
            "maize": 0.005,    # 0.5% per hour
            "beans": 0.008,    # 0.8% per hour
            "potatoes": 0.015, # 1.5% per hour
            "cabbage": 0.025,  # 2.5% per hour
            "other": 0.01      # 1% per hour
        }
        
        # Temperature multipliers
        self.temperature_factors = {
            10: 0.3,   # Very slow spoilage
            15: 0.5,   # Slow spoilage
            20: 0.8,   # Moderate spoilage
            25: 1.0,   # Base rate
            30: 1.5,   # Increased spoilage
            35: 2.2,   # High spoilage
            40: 3.0    # Very high spoilage
        }
    
    def predict_risk(self, crop_type: str, estimated_duration: int, weather_conditions: Dict) -> float:
        """
        Predict spoilage risk percentage (0-1)
        """
        try:
            # Get base spoilage rate
            base_rate = self.base_spoilage_rates.get(crop_type.lower(), self.base_spoilage_rates["other"])
            
            # Calculate temperature factor
            temperature = weather_conditions.get("temperature", 25)
            temp_factor = self._get_temperature_factor(temperature)
            
            # Calculate humidity factor
            humidity = weather_conditions.get("humidity", 60)
            humidity_factor = 1.0 + (humidity - 60) / 100  # Higher humidity increases spoilage
            
            # Calculate duration in hours
            duration_hours = estimated_duration / 60
            
            # Calculate spoilage probability
            spoilage_probability = 1 - np.exp(-base_rate * temp_factor * humidity_factor * duration_hours)
            
            # Cap at 95% to avoid 100% certainty
            return min(spoilage_probability, 0.95)
            
        except Exception as e:
            print(f"Error in spoilage prediction: {e}")
            return 0.1  # Default low risk
    
    def _get_temperature_factor(self, temperature: float) -> float:
        """Get temperature multiplier for spoilage rate"""
        # Find closest temperature in factors
        temps = list(self.temperature_factors.keys())
        closest_temp = min(temps, key=lambda x: abs(x - temperature))
        return self.temperature_factors[closest_temp]