# AgriConnect AI - Technical Implementation Guide

This guide provides technical implementation details for the most critical new features identified in the feature analysis.

---

## 1. Offline-First Architecture

### Architecture Overview
Implement a queue-based offline system that stores requests locally and syncs when connection is available.

### Implementation Steps

#### 1.1 Local Storage Layer
```python
# backend/app/offline/offline_storage.py
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class OfflineStorage:
    """Local storage for offline requests"""
    
    def __init__(self, db_path: str = "offline_requests.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize offline database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def store_request(self, request_type: str, data: Dict) -> int:
        """Store request for later sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO offline_requests (request_type, data)
            VALUES (?, ?)
        """, (request_type, json.dumps(data)))
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id
    
    def get_pending_requests(self, limit: int = 50) -> List[Dict]:
        """Get requests pending sync"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM offline_requests
            WHERE synced = 0
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_synced(self, request_id: int):
        """Mark request as synced"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE offline_requests
            SET synced = 1, synced_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))
        conn.commit()
        conn.close()
```

#### 1.2 Sync Service
```python
# backend/app/offline/sync_service.py
import asyncio
import httpx
from typing import List, Dict
from .offline_storage import OfflineStorage

class SyncService:
    """Service to sync offline requests when connection available"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.storage = OfflineStorage()
        self.syncing = False
    
    async def check_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_base_url}/health")
                return response.status_code == 200
        except:
            return False
    
    async def sync_pending_requests(self):
        """Sync all pending requests"""
        if self.syncing:
            return
        
        if not await self.check_connection():
            return
        
        self.syncing = True
        try:
            pending = self.storage.get_pending_requests()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for request in pending:
                    try:
                        # Route request to appropriate endpoint
                        endpoint = self._get_endpoint(request['request_type'])
                        response = await client.post(
                            f"{self.api_base_url}{endpoint}",
                            json=json.loads(request['data'])
                        )
                        
                        if response.status_code in [200, 201]:
                            self.storage.mark_synced(request['id'])
                    except Exception as e:
                        print(f"Failed to sync request {request['id']}: {e}")
                        # Increment sync attempts
                        self._increment_sync_attempts(request['id'])
        finally:
            self.syncing = False
    
    def _get_endpoint(self, request_type: str) -> str:
        """Map request type to API endpoint"""
        mapping = {
            'transport_request': '/api/v1/mcp/match-transport',
            'market_query': '/api/v1/mcp/market/query',
            'weather_query': '/api/v1/mcp/weather'
        }
        return mapping.get(request_type, '/api/v1/mcp/query')
    
    def _increment_sync_attempts(self, request_id: int):
        """Increment sync attempts counter"""
        # Implementation for retry logic
        pass
```

#### 1.3 USSD Offline Handler
```python
# Update backend/app/mcp_server/ussd_router.py
from app.offline.offline_storage import OfflineStorage
from app.offline.sync_service import SyncService

offline_storage = OfflineStorage()
sync_service = SyncService("http://localhost:8000")

@router.post("/ussd")
async def handle_ussd(request: Request, background_tasks: BackgroundTasks):
    """Enhanced USSD handler with offline support"""
    try:
        data = await request.json()
        session_id = data.get("sessionId")
        phone_number = data.get("phoneNumber")
        text = data.get("text", "").strip()
        
        # Check if this is a complete booking request
        if session.get("stage") == "route_optimization" and text == "1":
            # Store booking request offline if connection fails
            try:
                # Try to process online first
                response = await process_booking_online(session)
                return {"response": response}
            except Exception as e:
                # Store offline and return confirmation
                booking_data = {
                    "phone_number": phone_number,
                    "product": session["data"]["product"],
                    "quantity": session["data"]["quantity"],
                    "start_location": session["data"]["start_location"],
                    "destination": session["data"]["destination"],
                    "transporter": session["data"]["selected_transporter"]
                }
                request_id = offline_storage.store_request("transport_request", booking_data)
                
                # Trigger background sync
                background_tasks.add_task(sync_service.sync_pending_requests)
                
                return {
                    "response": (
                        "END ✅ Request saved offline!\n"
                        f"Request ID: {request_id}\n"
                        "We'll process when connection is available.\n"
                        "You'll receive SMS confirmation.\n"
                        "Thank you!"
                    )
                }
        
        # Continue with normal USSD flow...
        # ... existing code ...
        
    except Exception as e:
        return {"response": f"END Error: {str(e)}"}
```

---

## 2. Multi-Language Support

### Implementation

#### 2.1 Translation Service
```python
# backend/app/i18n/translations.py
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to AgriConnect USSD',
        'select_product': 'Select product to transport:',
        'enter_quantity': 'Enter quantity:',
        'booking_confirmed': 'Booking confirmed!',
        # ... more translations
    },
    'sn': {  # Shona
        'welcome': 'Mauya kuAgriConnect USSD',
        'select_product': 'Sarudza chigadzirwa chekutakura:',
        'enter_quantity': 'Pinda huwandu:',
        'booking_confirmed': 'Kubhuka kwakasimbiswa!',
        # ... more translations
    },
    'nd': {  # Ndebele
        'welcome': 'Siyakwamukela kuAgriConnect USSD',
        'select_product': 'Khetha umkhiqizo wokuthutha:',
        'enter_quantity': 'Faka inani:',
        'booking_confirmed': 'Ukubhuka kuqinisekisiwe!',
        # ... more translations
    }
}

class TranslationService:
    """Service for multi-language support"""
    
    def __init__(self, default_lang: str = 'en'):
        self.default_lang = default_lang
        self.translations = TRANSLATIONS
    
    def detect_language(self, phone_number: str, user_input: str = None) -> str:
        """Detect user's preferred language"""
        # Check user preference from database
        # Or detect from input text
        # Default to English
        return self.default_lang
    
    def translate(self, key: str, lang: str = None) -> str:
        """Get translation for key"""
        lang = lang or self.default_lang
        return self.translations.get(lang, self.translations['en']).get(
            key, 
            self.translations['en'].get(key, key)
        )
    
    def format_message(self, template_key: str, lang: str, **kwargs) -> str:
        """Format message with variables"""
        template = self.translate(template_key, lang)
        return template.format(**kwargs)
```

#### 2.2 Update USSD Router
```python
# Update backend/app/mcp_server/ussd_router.py
from app.i18n.translations import TranslationService

translator = TranslationService()

def show_welcome_menu(session: dict) -> str:
    """Show welcome menu in user's language"""
    lang = session.get('language', 'en')
    
    welcome_text = translator.translate('welcome', lang)
    menu_text = translator.translate('main_menu', lang)
    
    return f"CON {welcome_text}\n{menu_text}\n\nChoose option:"
```

---

## 3. Real-Time GPS Tracking

### Implementation

#### 3.1 GPS Tracking Service
```python
# backend/app/tracking/gps_tracker.py
from typing import Dict, Optional
from datetime import datetime
import asyncio

class GPSTracker:
    """Service for real-time GPS tracking"""
    
    def __init__(self, sms_service):
        self.sms_service = sms_service
        self.active_trackings = {}
    
    async def start_tracking(self, job_id: str, transporter_phone: str, 
                           farmer_phone: str, route_info: Dict):
        """Start tracking a transport job"""
        self.active_trackings[job_id] = {
            'transporter_phone': transporter_phone,
            'farmer_phone': farmer_phone,
            'route_info': route_info,
            'current_location': None,
            'last_update': datetime.now(),
            'milestones': self._calculate_milestones(route_info)
        }
        
        # Send initial tracking SMS
        await self.sms_service.send(
            farmer_phone,
            f"Tracking started for your order. You'll receive updates at key milestones."
        )
    
    async def update_location(self, job_id: str, lat: float, lon: float):
        """Update vehicle location"""
        if job_id not in self.active_trackings:
            return
        
        tracking = self.active_trackings[job_id]
        tracking['current_location'] = {'lat': lat, 'lon': lon}
        tracking['last_update'] = datetime.now()
        
        # Check if milestone reached
        milestone = self._check_milestone(tracking, lat, lon)
        if milestone:
            await self._send_milestone_update(job_id, milestone)
    
    def _calculate_milestones(self, route_info: Dict) -> List[Dict]:
        """Calculate key milestones for route"""
        # 25%, 50%, 75%, 90% of route
        milestones = []
        total_distance = route_info.get('distance_km', 0)
        
        for percent in [25, 50, 75, 90]:
            milestones.append({
                'percent': percent,
                'distance': total_distance * (percent / 100),
                'sent': False
            })
        
        return milestones
    
    async def _check_milestone(self, tracking: Dict, lat: float, lon: float) -> Optional[Dict]:
        """Check if milestone reached"""
        # Calculate progress based on current location
        # Compare with milestones
        # Return milestone if reached
        pass
    
    async def _send_milestone_update(self, job_id: str, milestone: Dict):
        """Send SMS update for milestone"""
        tracking = self.active_trackings[job_id]
        farmer_phone = tracking['farmer_phone']
        
        message = (
            f"Update: Your order is {milestone['percent']}% complete. "
            f"Estimated arrival in {milestone['eta']} minutes."
        )
        
        await self.sms_service.send(farmer_phone, message)
```

#### 3.2 GPS Update Endpoint
```python
# backend/app/mcp_server/mcp_tools.py
@router.post("/tracking/update")
async def update_gps_location(
    job_id: str,
    lat: float,
    lon: float,
    transporter_phone: str
):
    """Endpoint for transporters to update GPS location"""
    # Verify transporter has permission for this job
    # Update location in tracking service
    # Check for milestones and send alerts
    pass
```

---

## 4. Enhanced Spoilage Prediction

### Implementation

#### 4.1 ML-Based Spoilage Model
```python
# backend/app/ml/spoilage_predictor.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List
import pickle
from pathlib import Path

class MLSpoilagePredictor:
    """Machine learning-based spoilage prediction"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load existing model or train new one"""
        if self.model_path and Path(self.model_path).exists():
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            # Train new model with historical data
            self.model = self._train_model()
    
    def _train_model(self):
        """Train model with historical data"""
        # Load historical spoilage data
        # Features: crop_type, temperature, humidity, duration, packaging, handling
        # Target: spoilage_percentage
        
        # For now, use RandomForest
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # TODO: Load actual training data
        # X_train, y_train = load_training_data()
        # model.fit(X_train, y_train)
        
        return model
    
    def predict(self, features: Dict) -> Dict:
        """Predict spoilage risk"""
        # Extract features
        feature_vector = self._extract_features(features)
        
        # Predict
        risk_score = self.model.predict([feature_vector])[0]
        risk_score = max(0, min(1, risk_score))  # Clamp to [0, 1]
        
        # Get feature importance for explanation
        importance = self._get_feature_importance(features)
        
        return {
            'spoilage_risk': float(risk_score),
            'risk_level': self._classify_risk(risk_score),
            'factors': importance,
            'recommendations': self._generate_recommendations(features, risk_score)
        }
    
    def _extract_features(self, features: Dict) -> List[float]:
        """Extract feature vector from input"""
        # Encode categorical variables
        crop_type_encoding = {
            'tomatoes': 0, 'maize': 1, 'beans': 2,
            'potatoes': 3, 'cabbage': 4, 'other': 5
        }
        
        return [
            crop_type_encoding.get(features.get('crop_type', 'other'), 5),
            features.get('temperature', 25),
            features.get('humidity', 60),
            features.get('duration_hours', 2),
            features.get('packaging_quality', 0.5),  # 0-1 scale
            features.get('handling_quality', 0.5),   # 0-1 scale
            features.get('vehicle_type_refrigerated', 0),  # 0 or 1
        ]
    
    def _classify_risk(self, risk_score: float) -> str:
        """Classify risk level"""
        if risk_score > 0.7:
            return 'high'
        elif risk_score > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _get_feature_importance(self, features: Dict) -> Dict:
        """Get importance of each factor"""
        # Use model feature importance if available
        # Or calculate based on feature values
        return {
            'temperature': 'high' if features.get('temperature', 25) > 30 else 'low',
            'duration': 'high' if features.get('duration_hours', 2) > 4 else 'low',
            'packaging': 'high' if features.get('packaging_quality', 0.5) < 0.5 else 'low'
        }
    
    def _generate_recommendations(self, features: Dict, risk_score: float) -> List[str]:
        """Generate recommendations based on risk"""
        recommendations = []
        
        if risk_score > 0.5:
            recommendations.append("🔴 HIGH RISK: Use refrigerated transport immediately")
        
        if features.get('temperature', 25) > 30:
            recommendations.append("🌡️ High temperature: Reduce transport time or use cooling")
        
        if features.get('duration_hours', 2) > 4:
            recommendations.append("⏱️ Long duration: Consider faster route or split shipment")
        
        if features.get('packaging_quality', 0.5) < 0.5:
            recommendations.append("📦 Improve packaging quality to reduce spoilage")
        
        return recommendations
```

---

## 5. Market Price Forecasting

### Implementation

#### 5.1 Price Forecasting Service
```python
# backend/app/ml/price_forecaster.py
from prophet import Prophet
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta

class PriceForecaster:
    """Forecast market prices using Prophet"""
    
    def __init__(self):
        self.models = {}  # One model per product-market pair
    
    def train_model(self, product: str, market: str, historical_data: pd.DataFrame):
        """Train forecasting model"""
        # Prepare data for Prophet
        df = historical_data.rename(columns={
            'date': 'ds',
            'price': 'y'
        })
        
        # Create and train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(df)
        
        # Store model
        key = f"{product}_{market}"
        self.models[key] = model
    
    def forecast(self, product: str, market: str, days: int = 7) -> Dict:
        """Forecast prices for next N days"""
        key = f"{product}_{market}"
        
        if key not in self.models:
            # Return default forecast if model not trained
            return self._default_forecast(product, market, days)
        
        model = self.models[key]
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        
        # Extract forecast for future dates
        future_forecast = forecast.tail(days)
        
        return {
            'product': product,
            'market': market,
            'forecast': [
                {
                    'date': row['ds'].isoformat(),
                    'price': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper'])
                }
                for _, row in future_forecast.iterrows()
            ],
            'trend': self._calculate_trend(future_forecast),
            'recommendation': self._generate_recommendation(future_forecast)
        }
    
    def _calculate_trend(self, forecast: pd.DataFrame) -> str:
        """Calculate price trend"""
        first_price = forecast.iloc[0]['yhat']
        last_price = forecast.iloc[-1]['yhat']
        
        change = ((last_price - first_price) / first_price) * 100
        
        if change > 5:
            return 'increasing'
        elif change < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_recommendation(self, forecast: pd.DataFrame) -> str:
        """Generate recommendation based on forecast"""
        trend = self._calculate_trend(forecast)
        avg_price = forecast['yhat'].mean()
        
        if trend == 'increasing':
            return f"💰 Prices expected to rise. Consider selling in 2-3 days. Average: ${avg_price:.2f}/kg"
        elif trend == 'decreasing':
            return f"📉 Prices expected to fall. Consider selling soon. Average: ${avg_price:.2f}/kg"
        else:
            return f"📊 Prices expected to remain stable. Average: ${avg_price:.2f}/kg"
    
    def _default_forecast(self, product: str, market: str, days: int) -> Dict:
        """Return default forecast when model not available"""
        # Use current price with small random variation
        current_price = 2.50  # Get from market data
        
        forecast = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i+1)
            price = current_price * (1 + np.random.uniform(-0.1, 0.1))
            forecast.append({
                'date': date.isoformat(),
                'price': price,
                'lower_bound': price * 0.9,
                'upper_bound': price * 1.1
            })
        
        return {
            'product': product,
            'market': market,
            'forecast': forecast,
            'trend': 'stable',
            'recommendation': 'Forecast model not yet trained. Using estimates.'
        }
```

---

## 6. Payment Integration

### Implementation

#### 6.1 Mobile Money Integration
```python
# backend/app/payments/mobile_money.py
import httpx
from typing import Dict, Optional
from enum import Enum

class PaymentProvider(str, Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    MPESA = "mpesa"

class MobileMoneyService:
    """Service for mobile money payments"""
    
    def __init__(self, provider: PaymentProvider):
        self.provider = provider
        self.api_key = self._get_api_key()
        self.base_url = self._get_base_url()
    
    async def initiate_payment(self, amount: float, phone_number: str, 
                              reference: str) -> Dict:
        """Initiate mobile money payment"""
        if self.provider == PaymentProvider.ECOCASH:
            return await self._ecocash_payment(amount, phone_number, reference)
        elif self.provider == PaymentProvider.ONEMONEY:
            return await self._onemoney_payment(amount, phone_number, reference)
        # Add other providers
    
    async def _ecocash_payment(self, amount: float, phone_number: str, 
                              reference: str) -> Dict:
        """Process EcoCash payment"""
        # Integrate with EcoCash API
        # This is a placeholder - actual implementation depends on provider
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/ecocash/payment",
                json={
                    "amount": amount,
                    "phone_number": phone_number,
                    "reference": reference
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
    
    async def check_payment_status(self, transaction_id: str) -> Dict:
        """Check payment status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/payment/{transaction_id}/status",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
    
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        return os.getenv(f"{self.provider.upper()}_API_KEY", "")
    
    def _get_base_url(self) -> str:
        """Get API base URL"""
        urls = {
            PaymentProvider.ECOCASH: "https://api.ecocash.com",
            PaymentProvider.ONEMONEY: "https://api.onemoney.com",
        }
        return urls.get(self.provider, "")
```

#### 6.2 Payment Escrow
```python
# backend/app/payments/escrow.py
from enum import Enum
from datetime import datetime

class EscrowStatus(str, Enum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"

class EscrowService:
    """Service for payment escrow"""
    
    def __init__(self, mobile_money_service):
        self.mobile_money = mobile_money_service
        self.escrow_accounts = {}  # In production, use database
    
    async def create_escrow(self, job_id: str, amount: float, 
                           farmer_phone: str, transporter_phone: str) -> Dict:
        """Create escrow account for job"""
        # Hold payment from farmer
        payment = await self.mobile_money.initiate_payment(
            amount, farmer_phone, f"ESCROW_{job_id}"
        )
        
        self.escrow_accounts[job_id] = {
            'status': EscrowStatus.HELD,
            'amount': amount,
            'farmer_phone': farmer_phone,
            'transporter_phone': transporter_phone,
            'payment_reference': payment['transaction_id'],
            'created_at': datetime.now()
        }
        
        return {
            'escrow_id': job_id,
            'status': EscrowStatus.HELD,
            'message': 'Payment held in escrow. Will be released on delivery confirmation.'
        }
    
    async def release_payment(self, job_id: str, confirmation_code: str) -> Dict:
        """Release payment to transporter"""
        escrow = self.escrow_accounts.get(job_id)
        if not escrow:
            return {'error': 'Escrow not found'}
        
        # Verify confirmation code (from delivery confirmation)
        if not self._verify_confirmation(confirmation_code):
            return {'error': 'Invalid confirmation code'}
        
        # Release payment to transporter
        # In production, transfer to transporter's account
        escrow['status'] = EscrowStatus.RELEASED
        escrow['released_at'] = datetime.now()
        
        return {
            'escrow_id': job_id,
            'status': EscrowStatus.RELEASED,
            'message': 'Payment released to transporter'
        }
```

---

## Database Schema Updates

### New Tables Needed

```sql
-- Offline requests
CREATE TABLE offline_requests (
    id SERIAL PRIMARY KEY,
    request_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP,
    sync_attempts INTEGER DEFAULT 0
);

-- GPS tracking
CREATE TABLE gps_tracking (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lon DECIMAL(11, 8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2)
);

-- Payments
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    provider VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE,
    status VARCHAR(50) NOT NULL,
    farmer_phone VARCHAR(20) NOT NULL,
    transporter_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ratings
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    rater_type VARCHAR(20) NOT NULL, -- 'farmer' or 'transporter'
    rater_phone VARCHAR(20) NOT NULL,
    rated_phone VARCHAR(20) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    phone_number VARCHAR(20) PRIMARY KEY,
    language VARCHAR(10) DEFAULT 'en',
    notification_preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Testing Recommendations

1. **Unit Tests**: Test each service independently
2. **Integration Tests**: Test service interactions
3. **Load Tests**: Test system under high load
4. **Offline Tests**: Test offline functionality
5. **Language Tests**: Test all language translations
6. **Payment Tests**: Test payment flows (use sandbox)

---

## Deployment Considerations

1. **Environment Variables**: Store API keys, database URLs securely
2. **Database Migrations**: Use Alembic for schema changes
3. **Monitoring**: Set up logging and monitoring (Prometheus, Grafana)
4. **Backup**: Regular database backups
5. **Scaling**: Use load balancers, horizontal scaling
6. **Security**: HTTPS, rate limiting, input validation

---

*This guide provides implementation details for critical features. Adapt as needed for your specific requirements and infrastructure.*

