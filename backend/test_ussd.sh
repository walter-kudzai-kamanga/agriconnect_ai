#!/bin/bash

# Quick USSD Test Script
# Tests the USSD booking flow

SESSION_ID="test-$(date +%s)"
PHONE="+263771234567"
BASE_URL="http://localhost:8000/api/ussd"

echo "=========================================="
echo "AgriConnect USSD Test"
echo "=========================================="
echo "Session ID: $SESSION_ID"
echo "Phone: $PHONE"
echo ""

# Function to send USSD request
send_ussd() {
    local text=$1
    local step=$2
    
    if [ -n "$step" ]; then
        echo "--- Step $step ---"
    fi
    
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "{\"sessionId\":\"$SESSION_ID\",\"phoneNumber\":\"$PHONE\",\"text\":\"$text\"}")
    
    echo "$response" | python3 -m json.tool 2>/dev/null | grep -A 100 '"response"' | head -20
    echo ""
    
    # Extract response text
    echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])" 2>/dev/null
    echo ""
}

# Test flow
send_ussd "" "1: Welcome Menu"
read -p "Press Enter to continue..."

send_ussd "1" "2: Select Book Transport"
read -p "Press Enter to continue..."

send_ussd "1*1" "3: Select Location (Harare)"
read -p "Press Enter to continue..."

send_ussd "1*1*1" "4: Select Product (Tomatoes)"
read -p "Press Enter to continue..."

send_ussd "1*1*1*20" "5: Enter Quantity (20)"
read -p "Press Enter to continue..."

send_ussd "1*1*1*20*1" "6: Select Destination (Mbare Musika)"
read -p "Press Enter to continue..."

echo "=========================================="
echo "Test Complete!"
echo "=========================================="

