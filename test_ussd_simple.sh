#!/bin/bash

# Simple USSD Test - Quick Start
# Tests the USSD welcome menu

# Change port if your server runs on a different port
PORT=${1:-8080}
BASE_URL="http://localhost:${PORT}/api/ussd"

echo "Testing USSD Endpoint..."
echo "URL: $BASE_URL"
echo ""

# Test welcome menu
response=$(curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test-session-001",
    "phoneNumber": "+263771234567",
    "text": ""
  }')

echo "Response:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Extract and display the USSD response text
echo "USSD Menu:"
echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('response', 'No response'))
except:
    print('Error parsing response')
" 2>/dev/null || echo "Could not parse response"

echo ""
echo "✅ Test complete!"
echo ""
echo "To continue the flow, use:"
echo "  curl -X POST $BASE_URL \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"sessionId\":\"test-session-001\",\"phoneNumber\":\"+263771234567\",\"text\":\"1\"}'"

