#!/bin/bash
# Only log stderr, let stdout (JSON) pass through cleanly
exec /usr/local/bin/python3 /Users/user/Downloads/agriconnect-ai/backend/app/mcp_server/mcp_server.py 2>> /tmp/mcp_debug.log
