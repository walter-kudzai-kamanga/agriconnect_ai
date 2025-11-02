#!/usr/bin/env python3
"""
AgriConnect MCP Brain Server - Model Context Protocol Implementation
Provides intelligent farm-to-market orchestration via MCP protocol.
"""

import asyncio
import sys
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from datetime import datetime

# CRITICAL: Configure logging to stderr only (stdout is for MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
LOG = logging.getLogger("mcp_brain")

# Service URLs
WEATHER_SERVICE = "http://localhost:8001"
MARKET_SERVICE = "http://localhost:8002"
TRANSPORT_SERVICE = "http://localhost:8003"

class MCPBrainServer:
    """AgriConnect MCP Brain Server"""
    
    def __init__(self):
        self.tools = []
        self.resources = []
        self.prompts = []
        self.http_client = None
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    async def initialize_clients(self):
        """Initialize HTTP client for service communication"""
        self.http_client = httpx.AsyncClient(timeout=10.0)
        LOG.info("HTTP client initialized")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.http_client:
            await self.http_client.aclose()
            LOG.info("HTTP client closed")
    
    def _register_tools(self):
        """Register available MCP tools"""
        self.tools = [
            {
                "name": "query_farm_context",
                "description": "Get comprehensive farm context including weather, market prices, and transport availability. Returns intelligent analysis and recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "lon": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        },
                        "product": {
                            "type": "string",
                            "description": "Product name (e.g., tomatoes, maize, vegetables)"
                        },
                        "capacity": {
                            "type": "number",
                            "description": "Required transport capacity in kg",
                            "default": 500.0
                        }
                    },
                    "required": ["lat", "lon", "product"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get current weather conditions for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "description": "Latitude"},
                        "lon": {"type": "number", "description": "Longitude"}
                    },
                    "required": ["lat", "lon"]
                }
            },
            {
                "name": "get_market_prices",
                "description": "Get current market prices for a product",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product": {"type": "string", "description": "Product name"},
                        "lat": {"type": "number", "description": "Latitude"},
                        "lon": {"type": "number", "description": "Longitude"},
                        "radius_km": {"type": "number", "description": "Search radius", "default": 50}
                    },
                    "required": ["product", "lat", "lon"]
                }
            },
            {
                "name": "get_transport_options",
                "description": "Get available transport options for moving produce",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "description": "Pickup latitude"},
                        "lon": {"type": "number", "description": "Pickup longitude"},
                        "capacity": {"type": "number", "description": "Required capacity in kg"},
                        "perishable": {"type": "boolean", "description": "Is cargo perishable?", "default": True}
                    },
                    "required": ["lat", "lon", "capacity"]
                }
            },
            {
                "name": "predict_spoilage_risk",
                "description": "Predict spoilage risk for perishable products",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product": {"type": "string", "description": "Product name"},
                        "temperature": {"type": "number", "description": "Current temperature in Celsius"},
                        "duration_hours": {"type": "number", "description": "Expected transport duration"}
                    },
                    "required": ["product", "temperature", "duration_hours"]
                }
            }
        ]
    
    def _register_resources(self):
        """Register available MCP resources"""
        self.resources = [
            {
                "uri": "agriconnect://services/status",
                "name": "Service Status",
                "description": "Current status of all AgriConnect services",
                "mimeType": "application/json"
            },
            {
                "uri": "agriconnect://config/services",
                "name": "Service Configuration",
                "description": "Configuration for weather, market, and transport services",
                "mimeType": "application/json"
            }
        ]
    
    def _register_prompts(self):
        """Register available MCP prompts"""
        self.prompts = [
            {
                "name": "analyze_farm_operation",
                "description": "Analyze a farm operation and provide recommendations",
                "arguments": [
                    {
                        "name": "operation_type",
                        "description": "Type of operation (harvest, transport, market)",
                        "required": True
                    },
                    {
                        "name": "location",
                        "description": "Farm location (lat,lon)",
                        "required": True
                    }
                ]
            }
        ]
    
    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        await self.initialize_clients()
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False}
            },
            "serverInfo": {
                "name": "agriconnect-mcp-brain",
                "version": "2.0.0"
            }
        }
    
    async def handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request"""
        return {"tools": self.tools}
    
    async def handle_resources_list(self, params: Dict) -> Dict:
        """Handle resources/list request"""
        return {"resources": self.resources}
    
    async def handle_resources_read(self, params: Dict) -> Dict:
        """Handle resources/read request"""
        uri = params.get("uri", "")
        
        if uri == "agriconnect://services/status":
            status = await self._get_services_status()
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(status, indent=2)
                }]
            }
        elif uri == "agriconnect://config/services":
            config = {
                "weather_service": WEATHER_SERVICE,
                "market_service": MARKET_SERVICE,
                "transport_service": TRANSPORT_SERVICE
            }
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(config, indent=2)
                }]
            }
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    async def handle_prompts_list(self, params: Dict) -> Dict:
        """Handle prompts/list request"""
        return {"prompts": self.prompts}
    
    async def handle_prompts_get(self, params: Dict) -> Dict:
        """Handle prompts/get request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "analyze_farm_operation":
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Analyze this farm operation: {json.dumps(arguments, indent=2)}"
                    }
                }
            ]
            return {"messages": messages}
        
        raise ValueError(f"Unknown prompt: {name}")
    
    async def handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        LOG.info(f"Tool called: {tool_name}")
        
        try:
            if tool_name == "query_farm_context":
                result = await self._query_farm_context(arguments)
            elif tool_name == "get_weather":
                result = await self._get_weather(arguments)
            elif tool_name == "get_market_prices":
                result = await self._get_market_prices(arguments)
            elif tool_name == "get_transport_options":
                result = await self._get_transport_options(arguments)
            elif tool_name == "predict_spoilage_risk":
                result = await self._predict_spoilage_risk(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }
        
        except Exception as e:
            LOG.error(f"Tool execution error: {e}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error executing {tool_name}: {str(e)}"
                }],
                "isError": True
            }
    
    async def _query_farm_context(self, args: Dict) -> Dict:
        """Query comprehensive farm context"""
        lat = args.get("lat")
        lon = args.get("lon")
        product = args.get("product")
        capacity = args.get("capacity", 500.0)
        
        LOG.info(f"Querying farm context for {product} at ({lat}, {lon})")
        
        # Query all services concurrently
        tasks = [
            self._get_weather({"lat": lat, "lon": lon}),
            self._get_market_prices({"product": product, "lat": lat, "lon": lon}),
            self._get_transport_options({"lat": lat, "lon": lon, "capacity": capacity, "perishable": True})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        weather, market, transport = results
        
        # Handle partial failures
        if isinstance(weather, Exception):
            weather = {"error": str(weather), "status": "unavailable"}
        if isinstance(market, Exception):
            market = {"error": str(market), "status": "unavailable"}
        if isinstance(transport, Exception):
            transport = {"error": str(transport), "status": "unavailable"}
        
        # Perform intelligent analysis
        analysis = self._analyze_context(weather, market, transport, product)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "location": {"lat": lat, "lon": lon},
            "product": product,
            "data": {
                "weather": weather,
                "market": market,
                "transport": transport
            },
            "analysis": analysis
        }
    
    async def _get_weather(self, args: Dict) -> Dict:
        """Get weather data from weather service"""
        try:
            response = await self.http_client.post(
                f"{WEATHER_SERVICE}/weather",
                json={"location": {"lat": args["lat"], "lon": args["lon"]}, "units": "metric"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOG.error(f"Weather service error: {e}")
            # Return mock data for testing
            return {
                "status": "mock",
                "data": {
                    "temperature": 28,
                    "condition": "sunny",
                    "humidity": 65,
                    "description": "Clear skies"
                }
            }
    
    async def _get_market_prices(self, args: Dict) -> Dict:
        """Get market prices from market service"""
        try:
            response = await self.http_client.post(
                f"{MARKET_SERVICE}/market/query",
                json={
                    "product": args["product"],
                    "location": {"lat": args["lat"], "lon": args["lon"]},
                    "radius_km": args.get("radius_km", 50)
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOG.error(f"Market service error: {e}")
            # Return mock data for testing
            return {
                "status": "mock",
                "prices": [
                    {"market": "Central Market", "price": 2.50, "distance_km": 15},
                    {"market": "Farmers Market", "price": 2.75, "distance_km": 8}
                ],
                "average_price": 2.625
            }
    
    async def _get_transport_options(self, args: Dict) -> Dict:
        """Get transport options from transport service"""
        try:
            response = await self.http_client.post(
                f"{TRANSPORT_SERVICE}/transport/query",
                json={
                    "pickup_location": {"lat": args["lat"], "lon": args["lon"]},
                    "required_capacity_kg": args["capacity"],
                    "perishable": args.get("perishable", True)
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOG.error(f"Transport service error: {e}")
            # Return mock data for testing
            return {
                "status": "mock",
                "available_vehicles": [
                    {"vehicle_type": "refrigerated_truck", "capacity_kg": 1000, "cost_per_km": 1.5, "available": True},
                    {"vehicle_type": "pickup_truck", "capacity_kg": 500, "cost_per_km": 0.8, "available": True}
                ]
            }
    
    async def _predict_spoilage_risk(self, args: Dict) -> Dict:
        """Predict spoilage risk"""
        product = args["product"].lower()
        temp = args["temperature"]
        duration = args["duration_hours"]
        
        # Simple risk calculation
        base_risk = 0.1
        temp_factor = max(0, (temp - 25) / 25)  # Risk increases above 25°C
        duration_factor = duration / 24  # Risk per day
        
        risk = min(base_risk + (temp_factor * 0.3) + (duration_factor * 0.2), 1.0)
        
        return {
            "product": product,
            "spoilage_risk": round(risk, 3),
            "risk_level": "high" if risk > 0.5 else "medium" if risk > 0.3 else "low",
            "factors": {
                "temperature": temp,
                "duration_hours": duration
            },
            "recommendations": self._get_spoilage_recommendations(risk, temp)
        }
    
    def _get_spoilage_recommendations(self, risk: float, temp: float) -> List[str]:
        """Get recommendations based on spoilage risk"""
        recommendations = []
        
        if risk > 0.5:
            recommendations.append("🔴 HIGH RISK: Use refrigerated transport immediately")
        if temp > 30:
            recommendations.append("🌡️ High temperature: Reduce transport time or use cooling")
        if risk > 0.3:
            recommendations.append("⚠️ Consider faster delivery route")
        else:
            recommendations.append("✅ Risk acceptable with standard precautions")
        
        return recommendations
    
    def _analyze_context(self, weather: Dict, market: Dict, transport: Dict, product: str) -> Dict:
        """Analyze all context data and provide recommendations"""
        analysis = {
            "weather_score": 0.5,
            "market_score": 0.5,
            "transport_score": 0.5,
            "overall_score": 0.5,
            "recommendation": "",
            "insights": []
        }
        
        # Weather analysis
        if "data" in weather:
            temp = weather["data"].get("temperature", 25)
            condition = weather["data"].get("condition", "").lower()
            
            if "rain" in condition or "storm" in condition:
                analysis["weather_score"] = 0.3
                analysis["insights"].append("⚠️ Adverse weather - consider delaying")
            elif temp > 30:
                analysis["weather_score"] = 0.6
                analysis["insights"].append(f"🌡️ High temp ({temp}°C) - use refrigeration")
            else:
                analysis["weather_score"] = 1.0
                analysis["insights"].append("✅ Good weather conditions")
        
        # Market analysis
        if "prices" in market or "average_price" in market:
            avg_price = market.get("average_price", 0)
            if avg_price > 0:
                analysis["market_score"] = min(avg_price / 3.0, 1.0)
                analysis["insights"].append(f"💰 Market price: ${avg_price:.2f}/kg")
        
        # Transport analysis
        if "available_vehicles" in transport:
            vehicles = transport.get("available_vehicles", [])
            if vehicles:
                analysis["transport_score"] = 1.0
                analysis["insights"].append(f"🚚 {len(vehicles)} vehicles available")
            else:
                analysis["transport_score"] = 0.2
                analysis["insights"].append("⚠️ Limited transport options")
        
        # Calculate overall score
        analysis["overall_score"] = (
            analysis["weather_score"] +
            analysis["market_score"] +
            analysis["transport_score"]
        ) / 3
        
        # Generate recommendation
        if analysis["overall_score"] > 0.8:
            analysis["recommendation"] = "✅ EXCELLENT - Proceed immediately"
        elif analysis["overall_score"] > 0.6:
            analysis["recommendation"] = "🟢 GOOD - Proceed with standard precautions"
        elif analysis["overall_score"] > 0.4:
            analysis["recommendation"] = "🟡 MODERATE - Review carefully"
        else:
            analysis["recommendation"] = "🔴 POOR - Consider alternatives or delay"
        
        return analysis
    
    async def _get_services_status(self) -> Dict:
        """Check status of all services"""
        services = {
            "weather": WEATHER_SERVICE,
            "market": MARKET_SERVICE,
            "transport": TRANSPORT_SERVICE
        }
        
        status = {}
        for name, url in services.items():
            try:
                response = await self.http_client.get(f"{url}/health", timeout=3.0)
                status[name] = "healthy" if response.status_code == 200 else "degraded"
            except Exception:
                status[name] = "unavailable"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": status
        }
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        LOG.info(f"Handling: {method}")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            elif method == "resources/list":
                result = await self.handle_resources_list(params)
            elif method == "resources/read":
                result = await self.handle_resources_read(params)
            elif method == "prompts/list":
                result = await self.handle_prompts_list(params)
            elif method == "prompts/get":
                result = await self.handle_prompts_get(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            LOG.error(f"Request handling error: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


async def main():
    """Main MCP server loop - reads from stdin, writes to stdout"""
    LOG.info("=== AgriConnect MCP Brain Server Starting ===")
    LOG.info(f"Weather Service: {WEATHER_SERVICE}")
    LOG.info(f"Market Service: {MARKET_SERVICE}")
    LOG.info(f"Transport Service: {TRANSPORT_SERVICE}")
    
    server = MCPBrainServer()
    
    try:
        # Main protocol loop
        while True:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            
            if not line:
                LOG.info("EOF received, shutting down")
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse request
                request = json.loads(line)
                LOG.info(f"Request ID: {request.get('id')}, Method: {request.get('method')}")
                
                # Handle request
                response = await server.handle_request(request)
                
                # Write response to stdout (MUST be valid JSON)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                LOG.error(f"JSON decode error: {e}")
                # Skip malformed input, don't send error response
                continue
    
    finally:
        await server.cleanup()
        LOG.info("=== AgriConnect MCP Brain Server Stopped ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOG.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)