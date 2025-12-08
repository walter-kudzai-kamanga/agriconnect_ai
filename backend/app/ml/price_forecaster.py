import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import json

class PriceForecaster:
    """Forecast market prices using time-series analysis"""
    
    def __init__(self):
        self.historical_data = {}
        self._load_historical_data()
    
    def _load_historical_data(self):
        """Load historical price data"""
        # In production, load from database
        # For now, use mock historical data
        base_prices = {
            'tomatoes': 2.50,
            'maize': 1.20,
            'fresh vegetables': 3.10,
            'potatoes': 1.50,
            'fruits': 4.00
        }
        
        for product, base_price in base_prices.items():
            # Generate 30 days of historical data
            dates = []
            prices = []
            
            for i in range(30, 0, -1):
                date = datetime.now() - timedelta(days=i)
                # Add some realistic variation
                variation = np.random.uniform(-0.2, 0.2)
                price = base_price * (1 + variation)
                dates.append(date)
                prices.append(round(price, 2))
            
            self.historical_data[product] = {
                'dates': dates,
                'prices': prices
            }
    
    def forecast(self, product: str, market: str, days: int = 7) -> Dict:
        """Forecast prices for next N days"""
        if product not in self.historical_data:
            return self._default_forecast(product, market, days)
        
        historical = self.historical_data[product]
        prices = historical['prices']
        
        # Simple moving average with trend
        window = min(7, len(prices))
        recent_avg = np.mean(prices[-window:])
        trend = (prices[-1] - prices[-window]) / window if window > 1 else 0
        
        # Generate forecast
        forecast = []
        for i in range(1, days + 1):
            date = datetime.now() + timedelta(days=i)
            # Apply trend and some random variation
            predicted_price = recent_avg + (trend * i) + np.random.uniform(-0.1, 0.1)
            predicted_price = max(0.5, predicted_price)  # Ensure positive
            
            forecast.append({
                'date': date.isoformat(),
                'price': round(predicted_price, 2),
                'lower_bound': round(predicted_price * 0.9, 2),
                'upper_bound': round(predicted_price * 1.1, 2)
            })
        
        trend_direction = self._calculate_trend(forecast)
        
        return {
            'product': product,
            'market': market,
            'forecast': forecast,
            'trend': trend_direction,
            'current_price': prices[-1] if prices else 2.50,
            'recommendation': self._generate_recommendation(forecast, trend_direction)
        }
    
    def _calculate_trend(self, forecast: List[Dict]) -> str:
        """Calculate price trend"""
        if len(forecast) < 2:
            return 'stable'
        
        first_price = forecast[0]['price']
        last_price = forecast[-1]['price']
        change = ((last_price - first_price) / first_price) * 100
        
        if change > 5:
            return 'increasing'
        elif change < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_recommendation(self, forecast: List[Dict], trend: str) -> str:
        """Generate recommendation based on forecast"""
        avg_price = np.mean([f['price'] for f in forecast])
        
        if trend == 'increasing':
            return f"💰 Prices expected to rise. Consider selling in 2-3 days. Average: ${avg_price:.2f}/kg"
        elif trend == 'decreasing':
            return f"📉 Prices expected to fall. Consider selling soon. Average: ${avg_price:.2f}/kg"
        else:
            return f"📊 Prices expected to remain stable. Average: ${avg_price:.2f}/kg"
    
    def _default_forecast(self, product: str, market: str, days: int) -> Dict:
        """Return default forecast when model not available"""
        base_prices = {
            'tomatoes': 2.50,
            'maize': 1.20,
            'fresh vegetables': 3.10,
            'potatoes': 1.50,
            'fruits': 4.00
        }
        
        current_price = base_prices.get(product.lower(), 2.50)
        
        forecast = []
        for i in range(1, days + 1):
            date = datetime.now() + timedelta(days=i)
            price = current_price * (1 + np.random.uniform(-0.1, 0.1))
            forecast.append({
                'date': date.isoformat(),
                'price': round(price, 2),
                'lower_bound': round(price * 0.9, 2),
                'upper_bound': round(price * 1.1, 2)
            })
        
        return {
            'product': product,
            'market': market,
            'forecast': forecast,
            'trend': 'stable',
            'current_price': current_price,
            'recommendation': 'Forecast model not yet trained. Using estimates.'
        }

# Global instance
price_forecaster = PriceForecaster()

