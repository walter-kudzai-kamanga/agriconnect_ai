# USSD Usage Guide - AgriConnect AI

## Overview

AgriConnect AI provides a USSD (Unstructured Supplementary Service Data) interface that allows farmers to book transport using any basic mobile phone, without internet or a smartphone.

---

## How USSD Works

USSD is a menu-based system accessed by dialing a code (like `*384*765#`). Users navigate through menus by selecting numbers.

---

## USSD Flow Example

### Step-by-Step Booking Process

1. **Dial USSD Code**: `*384*765#`
2. **Welcome Menu** appears:
   ```
   🌱 Welcome to AgriConnect USSD
   Smart Farm-to-Market Transport
   
   1. 📦 Book Smart Transport
   2. 💰 Check Rates & Prices
   3. 🌤️ Weather Forecast
   4. ℹ️ Help & Support
   
   Choose option:
   ```
3. **Select 1** to book transport
4. **Select Location** (e.g., `1` for Harare)
5. **Select Product** (e.g., `1` for Tomatoes)
6. **Enter Quantity** (e.g., `20` crates)
7. **Select Destination** (e.g., `1` for Mbare Musika Market)
8. **View Weather Intelligence** and recommendations
9. **Select Transporter** from available options
10. **Receive Confirmation** with route details

---

## Testing USSD via API

### Endpoint
```
POST http://localhost:8000/api/ussd
```

### Request Format
```json
{
  "sessionId": "unique-session-id",
  "phoneNumber": "+263771234567",
  "text": ""
}
```

### Example: Start USSD Session

```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": ""
  }'
```

**Response:**
```
{
  "response": "CON 🌱 Welcome to AgriConnect USSD\nSmart Farm-to-Market Transport\n\n1. 📦 Book Smart Transport\n2. 💰 Check Rates & Prices\n3. 🌤️ Weather Forecast\n4. ℹ️ Help & Support\n\nChoose option:"
}
```

### Example: Navigate Through Menus

**Step 1: Select "Book Transport" (option 1)**
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1"
  }'
```

**Step 2: Select Location (e.g., Harare = 1)**
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1*1"
  }'
```

**Step 3: Select Product (e.g., Tomatoes = 1)**
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1*1*1"
  }'
```

**Step 4: Enter Quantity (e.g., 20)**
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1*1*1*20"
  }'
```

**Step 5: Select Destination (e.g., Mbare Musika = 1)**
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1*1*1*20*1"
  }'
```

---

## Complete Booking Flow Script

Here's a complete example that simulates a full booking:

```bash
#!/bin/bash

SESSION_ID="test-$(date +%s)"
PHONE="+263771234567"
BASE_URL="http://localhost:8000/api/ussd"

echo "Starting USSD booking flow..."
echo "Session ID: $SESSION_ID"
echo ""

# Step 1: Welcome menu
echo "Step 1: Welcome Menu"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"\"}" | jq -r '.response'
echo ""

# Step 2: Select "Book Transport" (1)
echo "Step 2: Selecting Book Transport"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"1\"}" | jq -r '.response'
echo ""

# Step 3: Select Location - Harare (1)
echo "Step 3: Selecting Location - Harare"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"1*1\"}" | jq -r '.response'
echo ""

# Step 4: Select Product - Tomatoes (1)
echo "Step 4: Selecting Product - Tomatoes"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"1*1*1\"}" | jq -r '.response'
echo ""

# Step 5: Enter Quantity - 20
echo "Step 5: Entering Quantity - 20"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"1*1*1*20\"}" | jq -r '.response'
echo ""

# Step 6: Select Destination - Mbare Musika (1)
echo "Step 6: Selecting Destination - Mbare Musika"
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"1*1*1*20*1\"}" | jq -r '.response'
echo ""

echo "Booking flow complete!"
```

---

## Available Options

### Main Menu Options
- **1** - Book Smart Transport
- **2** - Check Rates & Prices
- **3** - Weather Forecast
- **4** - Help & Support

### Locations
- **1** - Harare
- **2** - Bulawayo
- **3** - Mutare
- **4** - Gweru
- **5** - Masvingo
- **6** - Marondera
- **7** - Chitungwiza
- **8** - Kadoma

### Products
- **1** - Tomatoes (highly perishable)
- **2** - Maize (low perishability)
- **3** - Fresh Vegetables (highly perishable)
- **4** - Potatoes (medium perishability)
- **5** - Fruits (highly perishable)

### Destinations
- **1** - Mbare Musika Market
- **2** - Sakubva Market
- **3** - Renkini Market
- **4** - Gweru Main Market
- **5** - Masvingo Market
- **6** - Marondera Market
- **7** - Chitungwiza Market

---

## Integration with USSD Gateway

### For Production Use

To connect to a real USSD gateway (like AfricasTalking, Twilio, or local telecom provider), you need to:

1. **Configure USSD Gateway** to forward requests to your endpoint
2. **Map Gateway Format** to your API format

### Example Gateway Integration (AfricasTalking)

```python
# Gateway receives:
# {
#   "sessionId": "ATUid_xxx",
#   "phoneNumber": "263771234567",
#   "text": "1*1*1"
# }

# Your endpoint expects the same format, so it works directly!
```

### Example Gateway Integration (Custom Format)

If your gateway uses a different format, create an adapter:

```python
@router.post("/ussd/gateway")
async def handle_gateway_ussd(request: Request):
    """Adapter for custom USSD gateway format"""
    data = await request.json()
    
    # Transform gateway format to your format
    transformed = {
        "sessionId": data.get("session_id") or data.get("sessionId"),
        "phoneNumber": data.get("msisdn") or data.get("phoneNumber"),
        "text": data.get("ussd_string") or data.get("text", "")
    }
    
    # Call your existing handler
    return await handle_ussd_internal(transformed)
```

---

## Testing with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/ussd"
SESSION_ID = "test-session-001"
PHONE = "+263771234567"

def send_ussd(text=""):
    """Send USSD request"""
    response = requests.post(
        BASE_URL,
        json={
            "sessionId": SESSION_ID,
            "phoneNumber": PHONE,
            "text": text
        }
    )
    return response.json()["response"]

# Test flow
print("Welcome Menu:")
print(send_ussd(""))

print("\nSelect Book Transport:")
print(send_ussd("1"))

print("\nSelect Harare:")
print(send_ussd("1*1"))

print("\nSelect Tomatoes:")
print(send_ussd("1*1*1"))

print("\nEnter Quantity 20:")
print(send_ussd("1*1*1*20"))

print("\nSelect Mbare Musika:")
print(send_ussd("1*1*1*20*1"))
```

---

## Response Format

### CON (Continue)
Used for menus that require more input:
```
CON [menu text]
```

### END (End Session)
Used for final responses:
```
END [final message]
```

---

## Session Management

- **Session TTL**: 5 minutes (300 seconds)
- **Session Storage**: In-memory (use Redis for production)
- **Session ID**: Must be unique per user session

---

## Error Handling

If an error occurs, the system returns:
```
END Sorry, service temporarily unavailable. 
Please try again in 5 minutes.
For urgent help: 077-AGRICONNECT
```

---

## Quick Test Command

Test the welcome menu:
```bash
curl -X POST http://localhost:8000/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-001",
    "phoneNumber": "+263771234567",
    "text": ""
  }'
```

---

## Next Steps

1. **Test locally** using the curl commands above
2. **Integrate with USSD gateway** for production
3. **Configure USSD code** with telecom provider (e.g., `*384*765#`)
4. **Set up SMS notifications** for booking confirmations
5. **Add payment integration** for mobile money

---

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Test endpoint: `http://localhost:8000/api/ussd`
- API docs: `http://localhost:8000/docs`

