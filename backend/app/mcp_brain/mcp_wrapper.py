"""
MCP Server wrapper for AgriConnect API
This exposes your FastAPI endpoints as MCP tools
"""
import asyncio
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types


API_BASE_URL = "http://localhost:8000"

# Initialize MCP server
server = Server("agriconnect-mcp")

# Store auth token
auth_token = None

async def get_auth_token():
    """Get authentication token from your API"""
    global auth_token
    if auth_token:
        return auth_token
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/token",
            data={"username": "walter", "password": "wale"}
        )
        if response.status_code == 200:
            data = response.json()
            auth_token = data["access_token"]
            return auth_token
    return None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available MCP tools"""
    return [
        types.Tool(
            name="get_weather",
            description="Get weather information for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude"
                    },
                    "lon": {
                        "type": "number", 
                        "description": "Longitude"
                    }
                },
                "required": ["lat", "lon"]
            }
        ),
        types.Tool(
            name="get_market_trends",
            description="Get agricultural market trends and prices",
            inputSchema={
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Product name (e.g., tomatoes, maize, wheat)"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude"
                    }
                },
                "required": ["product", "lat", "lon"]
            }
        ),
        types.Tool(
            name="find_transport",
            description="Find available transport and optimize routes",
            inputSchema={
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Pickup latitude"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Pickup longitude"
                    },
                    "capacity": {
                        "type": "number",
                        "description": "Required capacity in kg"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product being transported"
                    }
                },
                "required": ["lat", "lon", "capacity", "product"]
            }
        ),
        types.Tool(
            name="full_analysis",
            description="Get comprehensive analysis including weather, market, and transport",
            inputSchema={
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Product name"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Location latitude"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Location longitude"
                    },
                    "capacity": {
                        "type": "number",
                        "description": "Capacity in kg",
                        "default": 500.0
                    }
                },
                "required": ["product", "lat", "lon"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls by routing to your FastAPI endpoints"""
    
    if not arguments:
        arguments = {}
    
    token = await get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    async with httpx.AsyncClient() as client:
        try:
            if name == "get_weather":
                # Call weather service through brain
                response = await client.post(
                    f"{API_BASE_URL}/query/simple",
                    params={
                        "product": "general",
                        "lat": arguments["lat"],
                        "lon": arguments["lon"]
                    },
                    headers=headers
                )
                data = response.json()
                weather_data = data.get("data", {}).get("weather", {})
                
                return [types.TextContent(
                    type="text",
                    text=f"Weather Information:\n{format_weather(weather_data)}"
                )]
            
            elif name == "get_market_trends":
                response = await client.post(
                    f"{API_BASE_URL}/query/simple",
                    params={
                        "product": arguments["product"],
                        "lat": arguments["lat"],
                        "lon": arguments["lon"]
                    },
                    headers=headers
                )
                data = response.json()
                market_data = data.get("data", {}).get("market", {})
                
                return [types.TextContent(
                    type="text",
                    text=f"Market Trends for {arguments['product']}:\n{format_market(market_data)}"
                )]
            
            elif name == "find_transport":
                response = await client.post(
                    f"{API_BASE_URL}/query/simple",
                    params={
                        "product": arguments["product"],
                        "lat": arguments["lat"],
                        "lon": arguments["lon"]
                    },
                    headers=headers
                )
                data = response.json()
                transport_data = data.get("data", {}).get("transport", {})
                
                return [types.TextContent(
                    type="text",
                    text=f"Transport Options:\n{format_transport(transport_data)}"
                )]
            
            elif name == "full_analysis":
                response = await client.post(
                    f"{API_BASE_URL}/query/simple",
                    params={
                        "product": arguments["product"],
                        "lat": arguments["lat"],
                        "lon": arguments["lon"]
                    },
                    headers=headers
                )
                data = response.json()
                
                result = "🌾 AgriConnect Full Analysis\n" + "="*50 + "\n\n"
                result += format_weather(data.get("data", {}).get("weather", {})) + "\n\n"
                result += format_market(data.get("data", {}).get("market", {})) + "\n\n"
                result += format_transport(data.get("data", {}).get("transport", {})) + "\n\n"
                
                analysis = data.get("analysis", {})
                result += f" Analysis:\n"
                result += f"  Combined Score: {analysis.get('combined_score', 0):.2f}/1.0\n"
                result += f"  Recommendation: {analysis.get('recommendation', 'N/A')}\n"
                result += f"\n  Insights:\n"
                for insight in analysis.get('insights', []):
                    result += f"    • {insight}\n"
                
                return [types.TextContent(type="text", text=result)]
            
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error calling {name}: {str(e)}"
            )]

def format_weather(data: dict) -> str:
    """Format weather data for display"""
    if "error" in data:
        return f" Weather service unavailable: {data.get('error')}"
    
    weather_info = data.get("data", {})
    return f""" Weather:
  Condition: {weather_info.get('condition', 'N/A')}
  Temperature: {weather_info.get('temperature', 'N/A')}°C
  Humidity: {weather_info.get('humidity', 'N/A')}%
  Wind Speed: {weather_info.get('wind_speed', 'N/A')} km/h"""

def format_market(data: dict) -> str:
    """Format market data for display"""
    if "error" in data:
        return f" Market service unavailable: {data.get('error')}"
    
    prices = data.get("prices", [])
    if not prices:
        return " Market: No price data available"
    
    result = " Market Prices:\n"
    for price in prices[:5]:  # Show top 5
        result += f"  • {price.get('market_name', 'Unknown')}: ${price.get('price', 0):.2f}/kg\n"
    return result

def format_transport(data: dict) -> str:
    """Format transport data for display"""
    if "error" in data:
        return f"Transport service unavailable: {data.get('error')}"
    
    vehicles = data.get("available_vehicles", [])
    if not vehicles:
        return " Transport: No vehicles available"
    
    result = f"Transport: {len(vehicles)} vehicles available\n"
    for vehicle in vehicles[:3]:  # Show top 3
        result += f"  • {vehicle.get('vehicle_type', 'Unknown')}: "
        result += f"{vehicle.get('capacity_kg', 0)}kg capacity, "
        result += f"${vehicle.get('cost_estimate', 0):.2f}\n"
    return result

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agriconnect-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())