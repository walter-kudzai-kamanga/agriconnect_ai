# AgriConnect MCP Brain - Knowledge Base

## Architecture

The MCP Brain orchestrates multiple MCP (Model Context Protocol) services:
- **Weather MCP** (port 8001): Real-time weather data
- **Market MCP** (port 8002): Agricultural market prices
- **Transport MCP** (port 8003): Logistics and transport coordination

## Key Features Implemented

### 1. Circuit Breaker Pattern
- Prevents cascading failures
- Opens after 5 consecutive failures
- 30-second cooldown period before retry
- Tracks failure count per service

### 2. Redis Caching
- 5-minute default TTL for MCP responses
- Graceful fallback if Redis unavailable
- Cache keys include service name and request hash

### 3. Rate Limiting
- Default: 60 requests per minute per user
- In-memory implementation (consider Redis for production)
- Returns 429 status when exceeded

### 4. Retry Logic
- 3 attempts per MCP service call
- Exponential backoff (2^attempt seconds)
- Handles timeouts and connection errors

### 5. Partial Failure Handling
- Services can fail independently
- Analysis proceeds with available data
- Error details returned in response

## Environment Variables

```bash
# Authentication
JWT_SECRET=your-secret-key-change-in-production

# MCP Service URLs
WEATHER_SERVICE_URL=http://localhost:8001
MARKET_SERVICE_URL=http://localhost:8002
TRANSPORT_SERVICE_URL=http://localhost:8003

# Redis (optional but recommended)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_REQUESTS=60  # per minute
RATE_LIMIT_WINDOW=60    # seconds
```

## Quick Start

### Using Startup Scripts (Recommended)

**Mac/Linux:**
```bash
cd backend
./start_all.sh    # Start all services
./stop_all.sh     # Stop all services
```

**Windows:**
```cmd
cd backend
start_all.bat     # Start all services
stop_all.bat      # Stop all services
```

The scripts will:
- Check Python installation
- Install dependencies if needed
- Start all 4 services (Weather, Market, Transport, Brain)
- Create logs in `backend/logs/`
- Show service URLs for testing

### Manual Start (Alternative)

```bash
# Terminal 1 - Weather MCP
cd backend/app/mcp_server/weather_servers
python3 main.py

# Terminal 2 - Market MCP
cd backend/app/mcp_server/market_server
python3 main.py

# Terminal 3 - Transport MCP
cd backend/app/mcp_server/transport_server
python3 main.py

# Terminal 4 - MCP Brain
cd backend/app/mcp_brain
python3 mcp_brain.py
```

## Testing

### Test Users
- Username: `walter`, Password: `wale` (admin role)
- Username: `johndoe`, Password: `secret` (admin role)
- Username: `alice`, Password: `secret2` (user role)

### Test Endpoints
- `GET /test-users` - List available test users
- `POST /query/simple?product=tomatoes` - Quick query test
- `GET /health` - Check service health
- `GET /metrics` - View system metrics (requires auth)

## Common Issues

### Startup Script Path Errors
**Fixed**: The `start_all.sh` script had incorrect relative paths. Services change into subdirectories (e.g., `app/mcp_server/weather_servers`) before starting, so logs need `../../../logs/` path, not `../../logs/`.

**Solution**: Always run `./stop_all.sh` before `./start_all.sh` to avoid port binding conflicts.

### Missing Dependencies
If services fail to start:
```bash
pip3 install pyjwt httpx redis sqlalchemy pydantic fastapi uvicorn
pip3 install --upgrade fastapi  # Ensure FastAPI 0.119+
```

### MCP Services Not Running
If you see "service unavailable" errors:
1. Check that weather/market/transport servers are running
2. Verify ports match environment variables
3. Check logs for connection errors

### Redis Connection Failed
Redis is optional. The system will work without it, but:
- No response caching
- Higher load on MCP services
- Consider running Redis for production

### Circuit Breaker Open
If you see "circuit breaker open" errors:
1. Wait 30 seconds for cooldown
2. Check if downstream service is responding
3. Review service logs for root cause

## Production Considerations

1. **Replace fake_users_db** with proper database authentication
2. **Use Redis** for distributed caching and rate limiting
3. **Set strong JWT_SECRET** in environment
4. **Configure health checks** in load balancer
5. **Monitor circuit breaker metrics** for service issues
6. **Add request logging** for debugging
7. **Implement proper password hashing** (bcrypt)

## API Flow

1. User authenticates → receives JWT token
2. Token included in subsequent requests
3. Rate limiter checks user quota
4. MCP services queried concurrently
5. Responses cached in Redis
6. Intelligent analysis performed
7. Unified response returned to user


## testing mcp with claude
1. navigate to app/mcp_server directory
2. run npx @modelcontextprotocol/inspector ./debug_mcp.sh
3. connects then test with claude
