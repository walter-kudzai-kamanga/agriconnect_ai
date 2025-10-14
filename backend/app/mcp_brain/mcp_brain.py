import requests
import math

def query_mcp_contexts(lat, lon, product, capacity, location):
    try:
        # Query MCP Servers
        weather = requests.post(
            "http://localhost:8001/query",
            json={"lat": lat, "lon": lon},
            timeout=3
        ).json()

        market = requests.post(
            "http://localhost:8002/query",
            json={"product": product},
            timeout=3
        ).json()

        transport = requests.post(
            "http://localhost:8003/query",
            json={"farmer_location": location, "required_capacity": capacity},
            timeout=3
        ).json()
    except Exception as e:
        return {"error": f"MCP query failed: {e}"}

    # Contextual Reasoning Logic
   

    # 1. Weather Influence
    good_weather = weather["description"] not in ["rain", "storm", "flood"]
    weather_score = 1.0 if good_weather else 0.5

    # 2. Market Ranking (price and distance)
    markets = market.get("markets", [])
    for m in markets:
        price_score = m["price_per_kg"] / max(m["price_per_kg"] for m in markets)
        distance_score = 1 / (1 + m["distance_km"])  # closer markets are better
        m["market_score"] = 0.7 * price_score + 0.3 * distance_score

    best_market = max(markets, key=lambda x: x["market_score"]) if markets else None

    # 3. Transport Availability
    trucks = transport.get("available_trucks", [])
    selected_truck = transport.get("selected_truck")
    truck_score = 1.0 if selected_truck else 0.0

    # 4. Combined Reasoning
    overall_score = (
        (best_market["market_score"] if best_market else 0) *
        weather_score *
        truck_score
    )

    
    # Final Decision Context
 
    decision = {
        "context_type": "integrated_decision",
        "status": "success" if overall_score > 0 else "failed",
        "confidence": round(overall_score, 2),
        "recommendation": {
            "best_market": best_market,
            "selected_truck": selected_truck,
            "weather": weather,
            "notes": "Ideal to transport now." if good_weather else "Delay transport due to poor weather."
        }
    }

    return decision
