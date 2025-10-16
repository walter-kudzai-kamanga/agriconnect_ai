from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# Add these models for SMS processing
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

# Add market price database
MARKET_PRICES = {
    "tomatoes": {
        "Mbare Musika": 2.50,
        "Sakubva Market": 2.30,
        "Renkini Market": 2.70,
        "Gweru Main Market": 2.40,
        "Masvingo Market": 2.35,
        "Marondera Market": 2.45,
        "Chitungwiza Market": 2.55,
        "National Average": 2.45
    },
    "maize": {
        "Mbare Musika": 1.20,
        "Sakubva Market": 1.15,
        "Renkini Market": 1.25,
        "Gweru Main Market": 1.18,
        "Masvingo Market": 1.16,
        "Marondera Market": 1.22,
        "Chitungwiza Market": 1.24,
        "National Average": 1.20
    },
    "fresh vegetables": {
        "Mbare Musika": 3.10,
        "Sakubva Market": 2.90,
        "Renkini Market": 3.20,
        "Gweru Main Market": 2.95,
        "Masvingo Market": 2.85,
        "Marondera Market": 3.05,
        "Chitungwiza Market": 3.15,
        "National Average": 3.03
    },
    "potatoes": {
        "Mbare Musika": 1.50,
        "Sakubva Market": 1.45,
        "Renkini Market": 1.55,
        "Gweru Main Market": 1.48,
        "Masvingo Market": 1.42,
        "Marondera Market": 1.52,
        "Chitungwiza Market": 1.53,
        "National Average": 1.49
    },
    "fruits": {
        "Mbare Musika": 4.00,
        "Sakubva Market": 3.80,
        "Renkini Market": 4.20,
        "Gweru Main Market": 3.90,
        "Masvingo Market": 3.75,
        "Marondera Market": 4.05,
        "Chitungwiza Market": 4.10,
        "National Average": 3.97
    }
}

# Add weather history database
WEATHER_HISTORY = {
    "Harare": {
        "last_7_days": [25, 26, 24, 27, 25, 23, 26],
        "average_temp": 25.1,
        "rain_days": 2,
        "trend": "stable"
    },
    "Mutare": {
        "last_7_days": [22, 23, 21, 24, 22, 20, 23],
        "average_temp": 22.1,
        "rain_days": 3,
        "trend": "slight_cooling"
    },
    "Bulawayo": {
        "last_7_days": [28, 29, 27, 30, 28, 26, 29],
        "average_temp": 28.1,
        "rain_days": 0,
        "trend": "warming"
    },
    "Marondera": {
        "last_7_days": [24, 25, 23, 26, 24, 22, 25],
        "average_temp": 24.1,
        "rain_days": 2,
        "trend": "stable"
    },
    "Gweru": {
        "last_7_days": [26, 27, 25, 28, 26, 24, 27],
        "average_temp": 26.1,
        "rain_days": 1,
        "trend": "stable"
    }
}

class SMSProcessor:
    """Process SMS messages for transport requests"""
    
    def __init__(self):
        self.product_keywords = {
            "tomatoes": ["tomato", "tomatoes", "tomat"],
            "maize": ["maize", "corn", "mealies"],
            "fresh vegetables": ["vegetables", "veggies", "greens", "cabbage", "spinach"],
            "potatoes": ["potato", "potatoes", "spuds"],
            "fruits": ["fruits", "fruit", "oranges", "apples", "bananas"]
        }
        
        self.location_keywords = {
            "harare": ["harare", "hre"],
            "mutare": ["mutare", "umtali"],
            "bulawayo": ["bulawayo", "byo", "bullies"],
            "marondera": ["marondera", "marondera"],
            "gweru": ["gweru", "gwelo"],
            "masvingo": ["masvingo", "fort victoria"],
            "chitungwiza": ["chitungwiza", "chitungwiza"],
            "mbare musika": ["mbare", "mbare musika", "mbare market"],
            "sakubva market": ["sakubva", "sakubva market"],
            "renkini market": ["renkini", "renkini market"]
        }
    
    def parse_sms_text(self, text: str) -> Optional[SMSProductRequest]:
        """Parse SMS text to extract product, quantity, locations"""
        text_lower = text.lower().strip()
        
        # Extract product
        product = self._extract_product(text_lower)
        if not product:
            return None
        
        # Extract quantity
        quantity = self._extract_quantity(text_lower)
        if not quantity:
            return None
        
        # Extract locations
        locations = self._extract_locations(text_lower)
        if len(locations) < 2:
            return None
        
        start_location, destination = locations[0], locations[1]
        
        return SMSProductRequest(
            product=product,
            quantity=quantity,
            start_location=start_location,
            destination=destination,
            farmer_phone=""  # Will be set from SMS from_number
        )
    
    def _extract_product(self, text: str) -> Optional[str]:
        """Extract product from SMS text"""
        for product, keywords in self.product_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return product
        return None
    
    def _extract_quantity(self, text: str) -> Optional[float]:
        """Extract quantity from SMS text"""
        # Look for patterns like "20kg", "20 kg", "20 kilograms", "20kgs"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*kgs?',
            r'(\d+(?:\.\d+)?)\s*kilograms?',
            r'(\d+(?:\.\d+)?)\s*kg',
            r'(\d+(?:\.\d+)?)\s*crates?',
            r'(\d+(?:\.\d+)?)\s*bags?',
            r'(\d+(?:\.\d+)?)\s*tons?',
            r'(\d+(?:\.\d+)?)\s*tonnes?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return float(matches[0])
        
        # Look for standalone numbers
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
        if numbers:
            return float(numbers[0])
        
        return None
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract locations from SMS text"""
        found_locations = []
        text_lower = text.lower()
        
        for location, keywords in self.location_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Standardize location names
                    standardized = self._standardize_location_name(location)
                    if standardized not in found_locations:
                        found_locations.append(standardized)
                    break
        
        return found_locations
    
    def _standardize_location_name(self, location: str) -> str:
        """Standardize location names"""
        standardization_map = {
            "harare": "Harare",
            "mutare": "Mutare", 
            "bulawayo": "Bulawayo",
            "marondera": "Marondera",
            "gweru": "Gweru",
            "masvingo": "Masvingo",
            "chitungwiza": "Chitungwiza",
            "mbare musika": "Mbare Musika Market",
            "sakubva market": "Sakubva Market",
            "renkini market": "Renkini Market"
        }
        return standardization_map.get(location.lower(), location.title())
    
    async def process_sms_request(self, sms_request: SMSProductRequest) -> SMSResponse:
        """Process SMS request and generate comprehensive response"""
        try:
            # Get best transport recommendation
            transport_info = await self._get_best_transport(
                sms_request.start_location,
                sms_request.product,
                sms_request.quantity
            )
            
            # Get weather history
            weather_info = self._get_weather_history(sms_request.start_location)
            
            # Get market prices
            price_info = self._get_market_prices(sms_request.product)
            
            # Generate route optimization
            route_info = await mcp_integration.optimize_route_mcp(
                sms_request.start_location,
                sms_request.destination,
                sms_request.product,
                sms_request.quantity
            )
            
            # Build comprehensive response
            response_message = self._build_sms_response(
                sms_request, transport_info, weather_info, price_info, route_info
            )
            
            return SMSResponse(
                to_number=sms_request.farmer_phone,
                message=response_message,
                status="success"
            )
            
        except Exception as e:
            return SMSResponse(
                to_number=sms_request.farmer_phone,
                message=f"Error processing request: {str(e)}. Please check format and try again.",
                status="error"
            )
    
    async def _get_best_transport(self, location: str, product: str, quantity: float) -> dict:
        """Get the best transport option for the request"""
        transporters = await mcp_integration.get_available_transporters(location, product, quantity)
        
        if not transporters:
            return {
                "available": False,
                "message": "No suitable transport available"
            }
        
        # Select best transporter based on rating and suitability
        best_transporter = max(transporters, key=lambda x: x["rating"])
        
        # Calculate estimated cost based on typical distances
        base_cost = quantity * 0.15  # $0.15 per kg base rate
        if product in ["tomatoes", "fresh vegetables", "fruits"]:
            base_cost *= 1.2  # Premium for perishables
        
        return {
            "available": True,
            "name": best_transporter["name"],
            "type": best_transporter["type"],
            "capacity": best_transporter["capacity"],
            "contact": best_transporter["phone"],
            "estimated_cost": round(base_cost, 2),
            "rating": best_transporter["rating"]
        }
    
    def _get_weather_history(self, location: str) -> dict:
        """Get weather history for location"""
        location_key = location.split()[0].lower()  # Get first word for matching
        
        for loc_key, weather_data in WEATHER_HISTORY.items():
            if loc_key.lower() in location_key or location_key in loc_key.lower():
                return weather_data
        
        # Default to Harare if location not found
        return WEATHER_HISTORY["Harare"]
    
    def _get_market_prices(self, product: str) -> dict:
        """Get market prices for product"""
        product_key = product.lower()
        for price_product, prices in MARKET_PRICES.items():
            if price_product in product_key or product_key in price_product:
                return {
                    "product": price_product,
                    "prices": prices,
                    "highest": max(prices.values()),
                    "lowest": min(prices.values()),
                    "average": sum(prices.values()) / len(prices)
                }
        
        # Default to tomatoes if product not found
        return {
            "product": "tomatoes",
            "prices": MARKET_PRICES["tomatoes"],
            "highest": max(MARKET_PRICES["tomatoes"].values()),
            "lowest": min(MARKET_PRICES["tomatoes"].values()),
            "average": sum(MARKET_PRICES["tomatoes"].values()) / len(MARKET_PRICES["tomatoes"])
        }
    
    def _build_sms_response(self, request: SMSProductRequest, transport: dict, 
                          weather: dict, prices: dict, route: RouteOptimization) -> str:
        """Build comprehensive SMS response"""
        response = "AGRICONNECT TRANSPORT SOLUTION\n"
        response += "=" * 30 + "\n\n"
        
        # Request summary
        response += "YOUR REQUEST:\n"
        response += f"Product: {request.product.title()}\n"
        response += f"Quantity: {request.quantity}kg\n"
        response += f"From: {request.start_location}\n"
        response += f"To: {request.destination}\n\n"
        
        # Best transport option
        response += "RECOMMENDED TRANSPORT:\n"
        if transport["available"]:
            response += f"Transporter: {transport['name']}\n"
            response += f"Vehicle: {transport['type']}\n"
            response += f"Capacity: {transport['capacity']}kg\n"
            response += f"Rating: {transport['rating']}/5\n"
            response += f"Contact: {transport['contact']}\n"
            response += f"Est Cost: ${transport['estimated_cost']}\n\n"
        else:
            response += transport["message"] + "\n\n"
        
        # Route information
        response += "OPTIMIZED ROUTE:\n"
        response += f"Route: {route.route}\n"
        response += f"Distance: {route.distance}\n"
        response += f"Time: {route.estimated_time}\n"
        response += f"Spoilage Risk: {route.spoilage_risk:.1f}%\n\n"
        
        # Weather history
        response += f"WEATHER HISTORY - {request.start_location}:\n"
        response += f"7-day Avg Temp: {weather['average_temp']}C\n"
        response += f"Rain Days (last 7): {weather['rain_days']}\n"
        response += f"Trend: {weather['trend'].replace('_', ' ').title()}\n\n"
        
        # Market prices
        response += f"MARKET PRICES - {prices['product'].title()} (per kg):\n"
        response += f"Highest: ${prices['highest']} ({self._get_market_with_price(prices['prices'], prices['highest'])})\n"
        response += f"Lowest: ${prices['lowest']} ({self._get_market_with_price(prices['prices'], prices['lowest'])})\n"
        response += f"National Avg: ${prices['average']:.2f}\n\n"
        
        # Key markets
        response += "KEY MARKETS:\n"
        key_markets = ["Mbare Musika", "Sakubva Market", "Renkini Market", "National Average"]
        for market in key_markets:
            if market in prices["prices"]:
                response += f"{market}: ${prices['prices'][market]}\n"
        
        response += "\n"
        
        # Recommendations
        response += "RECOMMENDATIONS:\n"
        for rec in route.recommendations[:3]:  # Top 3 recommendations
            response += f"- {rec}\n"
        
        response += "\n"
        response += "Reply YES to confirm booking or call 077-AGRICONNECT for help."
        
        return response
    
    def _get_market_with_price(self, prices: dict, target_price: float) -> str:
        """Get market name for a given price"""
        for market, price in prices.items():
            if abs(price - target_price) < 0.01:  # Account for floating point
                return market
        return "Unknown"

# Initialize SMS processor
sms_processor = SMSProcessor()

# Add SMS endpoint to your router
@router.post("/sms")
async def handle_sms(request: Request):
    """Handle incoming SMS messages for transport requests"""
    try:
        data = await request.json()
        
        sms_request = SMSRequest(
            from_number=data.get("from"),
            text=data.get("text", ""),
            timestamp=datetime.now()
        )
        
        # Parse SMS text
        product_request = sms_processor.parse_sms_text(sms_request.text)
        
        if not product_request:
            return {
                "response": SMSResponse(
                    to_number=sms_request.from_number,
                    message=(
                        "Could not understand your request. Please use format:\n"
                        "PRODUCT QUANTITY FROM_LOCATION TO DESTINATION\n"
                        "Example: Tomatoes 20kg Marondera to Mbare Musika\n"
                        "Supported products: Tomatoes, Maize, Vegetables, Potatoes, Fruits"
                    ),
                    status="error"
                ).dict()
            }
        
        # Set farmer phone number
        product_request.farmer_phone = sms_request.from_number
        
        # Process the request
        sms_response = await sms_processor.process_sms_request(product_request)
        
        return {"response": sms_response.dict()}
        
    except Exception as e:
        return {
            "response": SMSResponse(
                to_number=data.get("from", "unknown"),
                message=f"System error. Please try again later or call 077-AGRICONNECT.",
                status="error"
            ).dict()
        }

# Add a test endpoint for SMS (optional)
@router.post("/test-sms")
async def test_sms_parsing(text: str):
    """Test endpoint for SMS parsing"""
    result = sms_processor.parse_sms_text(text)
    if result:
        return {
            "success": True,
            "parsed_data": result.dict(),
            "processed_response": await sms_processor.process_sms_request(result)
        }
    else:
        return {
            "success": False,
            "error": "Could not parse SMS text",
            "suggested_format": "PRODUCT QUANTITY FROM_LOCATION TO DESTINATION"
        }

# Add this to your existing MCP integration class
async def confirm_booking(self, farmer_phone: str, transporter_phone: str, request: SMSProductRequest):
    """Confirm booking between farmer and transporter"""
    # This would send confirmation messages to both parties
    farmer_message = (
        f"Booking confirmed! {transporter_phone} will contact you shortly "
        f"for {request.quantity}kg of {request.product} from {request.start_location} to {request.destination}."
    )
    
    transporter_message = (
        f"New booking: {request.quantity}kg of {request.product} "
        f"from {request.start_location} to {request.destination}. "
        f"Farmer: {farmer_phone}"
    )
    
    # In production, integrate with SMS gateway here
    print(f"To Farmer {farmer_phone}: {farmer_message}")
    print(f"To Transporter {transporter_phone}: {transporter_message}")
    
    return True