# USSD Quick Test Guide

## Quick Test (Copy & Paste)

### Test 1: Welcome Menu
```bash
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": ""
  }'
```

### Test 2: Select "Book Transport" (Option 1)
```bash
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": "1"
  }'
```

### Test 3: Complete Flow (All Steps)
```bash
# Step 1: Welcome
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":""}'

# Step 2: Book Transport
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":"1"}'

# Step 3: Select Harare
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":"1*1"}'

# Step 4: Select Tomatoes
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":"1*1*1"}'

# Step 5: Enter Quantity 20
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":"1*1*1*20"}'

# Step 6: Select Mbare Musika
curl -X POST http://localhost:8080/api/ussd \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-001","phoneNumber":"+263771234567","text":"1*1*1*20*1"}'
```

## Using the Test Script

### Simple Test Script
```bash
./test_ussd_simple.sh
```

Or specify port:
```bash
./test_ussd_simple.sh 8000
```

### Interactive Test Script
```bash
cd backend
./test_ussd.sh
```

## Understanding the Response

### Response Format
```json
{
  "response": "CON 🌱 Welcome to AgriConnect USSD\n..."
}
```

- **CON** = Continue (more input needed)
- **END** = End session (final response)

### Response Types

**CON (Continue)** - Shows menu, expects input:
```
CON [menu text]
Choose option:
```

**END (End)** - Final response, session ends:
```
END ✅ TRANSPORT BOOKED SUCCESSFULLY!
...
```

## Request Parameters

- **sessionId**: Unique ID for this USSD session (keep same for one flow)
- **phoneNumber**: Farmer's phone number (format: +263771234567)
- **text**: User's input (use `*` to separate steps, e.g., "1*1*1")

## Common Patterns

### Start New Session
```json
{
  "sessionId": "new-session-123",
  "phoneNumber": "+263771234567",
  "text": ""
}
```

### Continue Session (same sessionId)
```json
{
  "sessionId": "new-session-123",  // Same ID
  "phoneNumber": "+263771234567",
  "text": "1"  // User selected option 1
}
```

### Multi-step Input
```json
{
  "sessionId": "new-session-123",
  "phoneNumber": "+263771234567",
  "text": "1*1*1*20"  // Selected 1, then 1, then 1, then entered 20
}
```

## Testing Tips

1. **Keep sessionId consistent** for one complete flow
2. **Use unique sessionId** for each new test
3. **Text format**: Use `*` to separate menu selections
4. **Empty text** (`""`) = Start new session / show menu
5. **Session expires** after 5 minutes of inactivity

## Troubleshooting

### Error: Connection refused
- Make sure server is running: `cd backend && ./run-app.sh`

### Error: No response
- Check server logs: `tail -f backend/logs/main-app.log`
- Verify endpoint: `curl http://localhost:8080/api/health`

### Wrong menu shown
- Check sessionId is consistent
- Session might have expired (5 min timeout)
- Start with empty text to reset

## Next Steps

1. Test the welcome menu (command above)
2. Try the complete booking flow
3. Integrate with real USSD gateway
4. Add SMS notifications for confirmations

