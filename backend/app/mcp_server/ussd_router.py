from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import json
import asyncio
import aiohttp
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for type safety
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

# USSD session storage with TTL (in production, use Redis)
ussd_sessions = {}
SESSION_TTL = 300  # 5 minutes

# Enhanced product database with crop-specific properties
PRODUCTS = {
    "1": {
        "name": "Tomatoes", 
        "unit": "crates",
        "perishability": "high",
        "ideal_temp": "15-25°C",
        "spoil_time": "2-3 days",
        "handling": "Avoid stacking, ventilate"
    },
    "2": {
        "name": "Maize", 
        "unit": "bags",
        "perishability": "low", 
        "ideal_temp": "room temp",
        "spoil_time": "6-12 months",
        "handling": "Keep dry, avoid moisture"
    },
    "3": {
        "name": "Fresh Vegetables", 
        "unit": "crates",
        "perishability": "high",
        "ideal_temp": "10-15°C", 
        "spoil_time": "3-5 days",
        "handling": "Refrigerate if possible"
    },
    "4": {
        "name": "Potatoes", 
        "unit": "bags",
        "perishability": "medium",
        "ideal_temp": "7-10°C",
        "spoil_time": "2-3 months", 
        "handling": "Keep cool and dark"
    },
    "5": {
        "name": "Fruits", 
        "unit": "crates", 
        "perishability": "high",
        "ideal_temp": "10-15°C",
        "spoil_time": "5-7 days",
        "handling": "Handle gently, avoid bruising"
    }
}

# Zimbabwe regions and towns
LOCATIONS = {
    "1": "Harare",
    "2": "Bulawayo", 
    "3": "Mutare",
    "4": "Gweru",
    "5": "Masvingo",
    "6": "Marondera",
    "7": "Chitungwiza",
    "8": "Kadoma"
}

# Market destinations
DESTINATIONS = {
    "1": "Mbare Musika Market",
    "2": "Sakubva Market", 
    "3": "Renkini Market",
    "4": "Gweru Main Market",
    "5": "Masvingo Market",
    "6": "Marondera Market",
    "7": "Chitungwiza Market"
}

class USSDSessionManager:
    """Manage USSD sessions with TTL and cleanup"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, session_id: str, phone_number: str):
        """Create a new USSD session"""
        self.sessions[session_id] = {
            "phone_number": phone_number,
            "stage": "welcome",
            "data": {},
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        return self.sessions[session_id]
    
    def get_session(self, session_id: str):
        """Get session with TTL check"""
        session = self.sessions.get(session_id)
        if session:
            # Check if session expired
            if (datetime.now() - session["last_activity"]).seconds > SESSION_TTL:
                del self.sessions[session_id]
                return None
            session["last_activity"] = datetime.now()
        return session
    
    def update_session(self, session_id: str, updates: dict):
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_activity"] = datetime.now()

session_manager = USSDSessionManager()

class AgriConnectMCPIntegration:
    """Integration with your MCP backend for intelligent decisions"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def get_weather_intelligence(self, location: str) -> dict:
        """Get enhanced weather data with agricultural insights"""
        try:
            async with aiohttp.ClientSession() as session:
                # This would call your MCP weather endpoint
                async with session.get(
                    f"{self.base_url}/mcp/weather/{location}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except:
            pass
        
        # Fallback to intelligent mock data
        return self._generate_smart_weather(location)
    
    def _generate_smart_weather(self, location: str) -> dict:
        """Generate intelligent mock weather data based on location patterns"""
        # Zimbabwe weather patterns by region
        regional_patterns = {
            "Harare": {"base_temp": 25, "rain_chance": 0.3, "humidity": 45},
            "Bulawayo": {"base_temp": 28, "rain_chance": 0.1, "humidity": 30},
            "Mutare": {"base_temp": 22, "rain_chance": 0.4, "humidity": 65},
            "Gweru": {"base_temp": 26, "rain_chance": 0.2, "humidity": 40},
            "Masvingo": {"base_temp": 27, "rain_chance": 0.15, "humidity": 35}
        }
        
        pattern = regional_patterns.get(location, regional_patterns["Harare"])
        
        # Add some realistic variation
        temp_variation = random.uniform(-3, 3)
        current_temp = pattern["base_temp"] + temp_variation
        
        # Determine conditions based on probabilities
        if random.random() < pattern["rain_chance"]:
            condition = "Light Rain" if random.random() < 0.7 else "Thunderstorms"
        else:
            condition = random.choice(["Sunny", "Partly Cloudy", "Clear"])
        
        return {
            "temperature": round(current_temp, 1),
            "condition": condition,
            "humidity": pattern["humidity"] + random.randint(-10, 10),
            "wind_speed": random.randint(5, 20),
            "rain_probability": int(pattern["rain_chance"] * 100)
        }
    
    async def optimize_route_mcp(self, start: str, end: str, product_type: str, quantity: int) -> RouteOptimization:
        """Get intelligent route optimization from MCP"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "start_location": start,
                    "destination": end,
                    "product_type": product_type,
                    "quantity": quantity
                }
                
                async with session.post(
                    f"{self.base_url}/mcp/optimize-route",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return RouteOptimization(**data)
        except:
            pass
        
        # Fallback to intelligent mock optimization
        return self._generate_smart_route(start, end, product_type, quantity)
    
    def _generate_smart_route(self, start: str, end: str, product_type: str, quantity: int) -> RouteOptimization:
        """Generate intelligent route optimization"""
        # Zimbabwe route knowledge base
        route_templates = {
            ("Harare", "Marondera"): [
                "Harare → Arcturus Rd → Marondera (45km)",
                "Harare → Mutare Rd → Marondera (48km)"
            ],
            ("Harare", "Mutare"): [
                "Harare → Rusape → Mutare (265km)",
                "Harare → Marondera → Mutare (270km)"
            ],
            ("Harare", "Bulawayo"): [
                "Harare → Kwekwe → Bulawayo (440km)",
                "Harare → Gweru → Bulawayo (435km)"
            ]
        }
        
        # Find best matching route
        route_key = (start, end)
        if route_key not in route_templates:
            route_key = (end, start)  # Try reverse
        
        if route_key in route_templates:
            routes = route_templates[route_key]
        else:
            routes = [f"{start} → Main Route → {end}"]
        
        # Select optimal route based on product type
        selected_route = routes[0]
        if product_type == "Tomatoes" and "Arcturus" in selected_route:
            selected_route += " 🛣️ Smooth road recommended"
        
        # Calculate intelligent timing and spoilage risk
        base_time = random.uniform(0.5, 6.0)  # 30 min to 6 hours
        distance = base_time * 60  # Assume 60km/h average
        
        # Adjust for product perishability
        product = next(p for p in PRODUCTS.values() if p["name"] == product_type)
        spoilage_risk = 5.0  # Base risk
        
        if product["perishability"] == "high":
            spoilage_risk += 15.0
            base_time *= 0.9  # Faster routes for perishables
        
        if quantity > 1000:  # Large quantities
            base_time *= 1.2
            spoilage_risk += 5.0
        
        # Generate intelligent recommendations
        recommendations = self._generate_recommendations(product_type, start)
        
        return RouteOptimization(
            route=selected_route,
            estimated_time=f"{base_time:.1f} hours",
            distance=f"{distance:.1f} km",
            cost_estimate=quantity * 0.15,  # $0.15 per kg
            spoilage_risk=min(spoilage_risk, 30.0),  # Cap at 30%
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, product_type: str, location: str) -> List[str]:
        """Generate intelligent transport recommendations"""
        recommendations = []
        product = next(p for p in PRODUCTS.values() if p["name"] == product_type)
        
        # Product-specific recommendations
        if product["perishability"] == "high":
            recommendations.append("🚛 Use refrigerated transport")
            recommendations.append("⏱️ Minimize transit time")
            recommendations.append("📦 Use ventilated packaging")
        
        if product_type == "Tomatoes":
            recommendations.append("🍅 Avoid stacking crates")
            recommendations.append("🌡️ Maintain 15-25°C temperature")
        
        elif product_type == "Maize":
            recommendations.append("🌽 Keep bags dry and covered")
            recommendations.append("🚚 Standard truck transport suitable")
        
        # Location-specific recommendations
        if location in ["Mutare", "Marondera"]:
            recommendations.append("🌧️ Check weather - rain likely")
        
        if "Market" in location:
            recommendations.append("🕒 Arrive before 8AM for best prices")
        
        return recommendations[:4]  # Return top 4 recommendations
    
    async def get_available_transporters(self, location: str, product_type: str, quantity: int) -> List[dict]:
        """Get suitable transporters based on requirements"""
        # Mock transporter database
        all_transporters = [
            {
                "id": "1",
                "name": "Chido Transport",
                "type": "Refrigerated Truck",
                "capacity": 2000,
                "cost_per_km": 0.12,
                "rating": 4.5,
                "phone": "0771234567",
                "specialties": ["perishables", "fragile"]
            },
            {
                "id": "2", 
                "name": "Tafara Logistics",
                "type": "General Truck",
                "capacity": 2500,
                "cost_per_km": 0.10,
                "rating": 4.2,
                "phone": "0772345678",
                "specialties": ["grains", "bulk"]
            },
            {
                "id": "3",
                "name": "Fresh Van Co.",
                "type": "Refrigerated Van", 
                "capacity": 800,
                "cost_per_km": 0.15,
                "rating": 4.7,
                "phone": "0773456789",
                "specialties": ["perishables", "urgent"]
            }
        ]
        
        # Filter transporters based on requirements
        suitable = []
        for transporter in all_transporters:
            # Check capacity
            if transporter["capacity"] < quantity:
                continue
            
            # Check suitability for product type
            product = next(p for p in PRODUCTS.values() if p["name"] == product_type)
            if product["perishability"] == "high" and "perishables" not in transporter["specialties"]:
                continue
            
            suitable.append(transporter)
        
        return suitable[:3]  # Return top 3 suitable transporters

mcp_integration = AgriConnectMCPIntegration()

@router.post("/ussd")
async def handle_ussd(request: Request, background_tasks: BackgroundTasks):
    """Enhanced USSD handler with intelligent decision making"""
    try:
        data = await request.json()
        
        session_id = data.get("sessionId")
        phone_number = data.get("phoneNumber")
        text = data.get("text", "").strip()
        
        # Get or create session
        session = session_manager.get_session(session_id)
        if not session:
            session = session_manager.create_session(session_id, phone_number)
        
        response = await process_ussd_flow(text, session, session_id)
        
        # Update session
        session_manager.update_session(session_id, session)
        
        return {"response": response}
        
    except Exception as e:
        # Log the error for debugging
        print(f"USSD Error: {e}")
        return {
            "response": (
                "END Sorry, service temporarily unavailable. "
                "Please try again in 5 minutes.\n"
                "For urgent help: 077-AGRICONNECT"
            )
        }

async def process_ussd_flow(text: str, session: dict, session_id: str) -> str:
    """Process USSD input with intelligent flow management"""
    
    if text == "":
        return show_welcome_menu(session)
    
    current_stage = session["stage"]
    user_input = text.split('*')[-1]  # Get last input
    
    # Main flow router
    flow_handlers = {
        "welcome": handle_welcome,
        "main_menu": handle_main_menu,
        "select_location": handle_location_selection,
        "select_product": handle_product_selection, 
        "enter_quantity": handle_quantity_input,
        "select_destination": handle_destination_selection,
        "weather_intelligence": handle_weather_intelligence,
        "select_transporter": handle_transporter_selection,
        "route_optimization": handle_route_optimization
    }
    
    handler = flow_handlers.get(current_stage, handle_unknown_input)
    return await handler(user_input, session, session_id)

def show_welcome_menu(session: dict) -> str:
    """Show enhanced welcome menu"""
    session["stage"] = "main_menu"
    
    return (
        "CON 🌱 Welcome to AgriConnect USSD\n"
        "Smart Farm-to-Market Transport\n\n"
        "1. 📦 Book Smart Transport\n"
        "2. 💰 Check Rates & Prices\n" 
        "3. 🌤️ Weather Forecast\n"
        "4. ℹ️ Help & Support\n\n"
        "Choose option:"
    )

async def handle_welcome(input: str, session: dict, session_id: str) -> str:
    """Handle welcome input"""
    return show_welcome_menu(session)

async def handle_main_menu(input: str, session: dict, session_id: str) -> str:
    """Handle main menu selection"""
    if input == "1":
        session["stage"] = "select_location"
        return show_location_menu(session)
    elif input == "2":
        return show_transport_rates(session)
    elif input == "3":
        session["stage"] = "select_location"
        session["weather_only"] = True
        return show_location_menu(session)
    elif input == "4":
        return show_help_info(session)
    else:
        return "CON Invalid choice. Please select 1-4:\n"

def show_location_menu(session: dict) -> str:
    """Show location selection menu"""
    menu = "CON 📍 Select your location:\n"
    for num, location in LOCATIONS.items():
        menu += f"{num}. {location}\n"
    menu += "\nEnter choice:"
    return menu

async def handle_location_selection(input: str, session: dict, session_id: str) -> str:
    """Handle location selection"""
    if input in LOCATIONS:
        session["data"]["start_location"] = LOCATIONS[input]
        
        if session.get("weather_only"):
            # User only wants weather info
            return await show_weather_intelligence(session, session_id)
        else:
            session["stage"] = "select_product"
            return show_product_menu(session)
    else:
        return "CON Invalid location. Please choose 1-8:\n"

def show_product_menu(session: dict) -> str:
    """Show product selection menu"""
    menu = "CON 🍅 Select product to transport:\n"
    for num, product in PRODUCTS.items():
        perishable_icon = "🚨" if product["perishability"] == "high" else "📦"
        menu += f"{num}. {perishable_icon} {product['name']}\n"
    menu += "\nEnter choice:"
    return menu

async def handle_product_selection(input: str, session: dict, session_id: str) -> str:
    """Handle product selection"""
    if input in PRODUCTS:
        session["data"]["product"] = PRODUCTS[input]["name"]
        session["data"]["product_info"] = PRODUCTS[input]
        session["stage"] = "enter_quantity"
        
        product = PRODUCTS[input]
        return (
            f"CON Enter quantity of {product['name']}:\n"
            f"Unit: {product['unit']}\n"
            f"Example: 10 ({product['unit']})\n\n"
            f"Quantity:"
        )
    else:
        return "CON Invalid product. Please choose 1-5:\n"

async def handle_quantity_input(input: str, session: dict, session_id: str) -> str:
    """Handle quantity input with validation"""
    try:
        quantity = int(input)
        if quantity <= 0:
            raise ValueError
        
        session["data"]["quantity"] = quantity
        session["stage"] = "select_destination"
        return show_destination_menu(session)
        
    except ValueError:
        product = session["data"]["product_info"]
        return f"CON ❌ Invalid quantity. Please enter a number:\nQuantity ({product['unit']}):"

def show_destination_menu(session: str) -> str:
    """Show destination selection menu"""
    menu = "CON 🎯 Select destination market:\n"
    for num, destination in DESTINATIONS.items():
        menu += f"{num}. {destination}\n"
    menu += "\nEnter choice:"
    return menu

async def handle_destination_selection(input: str, session: dict, session_id: str) -> str:
    """Handle destination selection"""
    if input in DESTINATIONS:
        session["data"]["destination"] = DESTINATIONS[input]
        session["stage"] = "weather_intelligence"
        return await show_weather_intelligence(session, session_id)
    else:
        return "CON Invalid destination. Please choose 1-7:\n"

async def show_weather_intelligence(session: dict, session_id: str) -> str:
    """Show intelligent weather report with recommendations"""
    location = session["data"]["start_location"]
    
    # Get weather data from MCP
    weather_data = await mcp_integration.get_weather_intelligence(location)
    
    # Build weather report
    report = f"CON 🌤️ WEATHER INTELLIGENCE - {location}\n"
    report += f"Temp: {weather_data['temperature']}°C\n"
    report += f"Conditions: {weather_data['condition']}\n"
    report += f"Humidity: {weather_data['humidity']}%\n"
    report += f"Rain Chance: {weather_data['rain_probability']}%\n\n"
    
    # Add intelligent recommendations
    report += "📋 RECOMMENDATIONS:\n"
    
    if weather_data['rain_probability'] > 50:
        report += "• 🌧️ Use waterproof covering\n"
    if weather_data['temperature'] > 28:
        report += "• 🔥 Avoid midday transport\n"
    if weather_data['condition'] == "Thunderstorms":
        report += "• ⚡ Delay if possible\n"
    
    if session.get("weather_only"):
        report += "\n0. Main Menu\n"
        session["stage"] = "weather_done"
    else:
        # Product-specific advice
        if "product_info" in session["data"]:
            product = session["data"]["product_info"]
            if product["perishability"] == "high":
                report += f"• ❄️ {product['handling']}\n"
        
        report += "\n1. Continue to Transport\n2. Cancel\nChoose:"
        session["stage"] = "weather_intelligence"
    
    return report

async def handle_weather_intelligence(input: str, session: dict, session_id: str) -> str:
    """Handle weather intelligence continuation"""
    if session.get("weather_only"):
        if input == "0":
            session["stage"] = "main_menu"
            return show_welcome_menu(session)
        else:
            return "END Thank you for using AgriConnect Weather!"
    
    if input == "1":
        session["stage"] = "select_transporter"
        return await show_transporter_options(session)
    elif input == "2":
        return end_session("Booking cancelled. Thank you!")
    else:
        return "CON Please choose 1 or 2:"

async def show_transporter_options(session: dict) -> str:
    """Show intelligent transporter recommendations"""
    location = session["data"]["start_location"]
    product = session["data"]["product"]
    quantity = session["data"]["quantity"]
    
    # Get suitable transporters from MCP
    transporters = await mcp_integration.get_available_transporters(location, product, quantity)
    
    if not transporters:
        return (
            "END ❌ No suitable transport available.\n"
            "Try reducing quantity or different product.\n"
            "Support: 077-AGRICONNECT"
        )
    
    menu = "CON 🚚 SMART TRANSPORT OPTIONS:\n\n"
    
    for i, transporter in enumerate(transporters, 1):
        rating_stars = "⭐" * int(transporter["rating"])
        menu += f"{i}. {transporter['name']}\n"
        menu += f"   Type: {transporter['type']}\n"
        menu += f"   Capacity: {transporter['capacity']}kg\n"
        menu += f"   Rating: {rating_stars}\n"
        menu += f"   Contact: {transporter['phone']}\n\n"
    
    menu += "Choose transporter (1-3):"
    session["data"]["available_transporters"] = transporters
    return menu

async def handle_transporter_selection(input: str, session: dict, session_id: str) -> str:
    """Handle transporter selection"""
    try:
        choice_idx = int(input) - 1
        transporters = session["data"]["available_transporters"]
        
        if 0 <= choice_idx < len(transporters):
            session["data"]["selected_transporter"] = transporters[choice_idx]
            session["stage"] = "route_optimization"
            return await show_route_optimization(session)
        else:
            raise ValueError
            
    except (ValueError, KeyError):
        return "CON Invalid choice. Please select 1-3:"

async def show_route_optimization(session: dict) -> str:
    """Show intelligent route optimization results"""
    start = session["data"]["start_location"]
    destination = session["data"]["destination"]
    product = session["data"]["product"]
    quantity = session["data"]["quantity"]
    transporter = session["data"]["selected_transporter"]
    
    # Get optimized route from MCP
    route_info = await mcp_integration.optimize_route_mcp(start, destination, product, quantity)
    
    # Build final confirmation
    response = "END ✅ TRANSPORT BOOKED SUCCESSFULLY!\n\n"
    response += "📋 ORDER DETAILS:\n"
    response += f"Product: {product}\n"
    response += f"Quantity: {quantity}kg\n"
    response += f"From: {start}\n"
    response += f"To: {destination}\n"
    response += f"Transporter: {transporter['name']}\n\n"
    
    response += "🗺️ OPTIMIZED ROUTE:\n"
    response += f"Route: {route_info.route}\n"
    response += f"Distance: {route_info.distance}\n"
    response += f"Time: {route_info.estimated_time}\n"
    response += f"Cost: ${route_info.cost_estimate:.2f}\n"
    response += f"Spoilage Risk: {route_info.spoilage_risk:.1f}%\n\n"
    
    response += "💡 INTELLIGENT TIPS:\n"
    for tip in route_info.recommendations:
        response += f"• {tip}\n"
    
    response += f"\n📞 Contact {transporter['name']} at {transporter['phone']}\n"
    response += "Thank you for using AgriConnect! 🌱"
    
    # In production, save this booking to database
    await save_booking_to_database(session, route_info)
    
    return response

async def handle_route_optimization(input: str, session: dict, session_id: str) -> str:
    """Handle route optimization completion"""
    return end_session("Session completed. Thank you!")

async def save_booking_to_database(session: dict, route_info: RouteOptimization):
    """Save booking to database (placeholder for actual implementation)"""
    # This would save to your database in production
    booking_data = {
        "farmer_phone": session["phone_number"],
        "product": session["data"]["product"],
        "quantity": session["data"]["quantity"],
        "start_location": session["data"]["start_location"],
        "destination": session["data"]["destination"],
        "transporter": session["data"]["selected_transporter"]["name"],
        "route_info": route_info.dict(),
        "timestamp": datetime.now().isoformat()
    }
    print(f"Booking saved: {booking_data}")  # Replace with actual DB save

def show_transport_rates(session: dict) -> str:
    """Show transport rates"""
    rates = (
        "END 💰 TRANSPORT RATES (per km):\n\n"
        "Refrigerated Truck: $0.12-0.15/km\n"
        "General Truck: $0.10-0.12/km\n" 
        "Van: $0.15-0.18/km\n"
        "Pickup: $0.20-0.25/km\n\n"
        "Minimum charge: $10\n"
        "Free for orders > 500kg\n\n"
        "Dial *384*765# to book"
    )
    return end_session(rates)

def show_help_info(session: dict) -> str:
    """Show help information"""
    help_text = (
        "END ℹ️ AGRICONNECT HELP\n\n"
        "Book smart farm transport:\n"
        "1. Select location & product\n"
        "2. Get weather intelligence\n"
        "3. Choose optimal transport\n"
        "4. Receive route optimization\n\n"
        "Support: 077-AGRICONNECT\n"
        "Email: help@agriconnect.africa\n\n"
        "Dial *384*765# to start"
    )
    return end_session(help_text)

async def handle_unknown_input(input: str, session: dict, session_id: str) -> str:
    """Handle unknown input"""
    return "CON Invalid input. Please try again or dial 077-AGRICONNECT for help."

def end_session(message: str) -> str:
    """End USSD session with message"""
    return f"END {message}"

# Background task to clean up expired sessions
@router.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(cleanup_expired_sessions())

async def cleanup_expired_sessions():
    """Clean up expired USSD sessions"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in session_manager.sessions.items()
            if (current_time - session["last_activity"]).seconds > SESSION_TTL
        ]
        for session_id in expired_sessions:
            del session_manager.sessions[session_id]
        if expired_sessions:
            print(f"Cleaned up {len(expired_sessions)} expired sessions")