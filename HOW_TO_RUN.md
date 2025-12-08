# How to Run AgriConnect AI

## ✅ Server is Running!

The application is currently running on **port 8080**.

- **Dashboard**: http://localhost:8080
- **API Health**: http://localhost:8080/api/health
- **API Docs**: http://localhost:8080/docs

---

## Quick Start Methods

### Method 1: From Project Root (Easiest)
```bash
cd /home/deuce/agriconnect_ai
./run.sh
```
This automatically:
- Changes to backend directory
- Activates venv
- Sets PYTHONPATH
- Starts the server on port 8000

### Method 2: From Backend Directory
```bash
cd /home/deuce/agriconnect_ai/backend
./run-app.sh
```
Or specify a custom port:
```bash
./run-app.sh 8080
```

### Method 3: Manual (Full Control)
```bash
cd /home/deuce/agriconnect_ai/backend
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 4: Start All Services
```bash
cd /home/deuce/agriconnect_ai/backend
./start_all.sh
```
This starts:
- Main FastAPI app (port 8000)
- Weather MCP service (port 8001)
- Market MCP service (port 8002)
- Transport MCP service (port 8003)

---

## Common Issues & Solutions

### ❌ Error: "No module named 'app'"
**Cause**: Running from wrong directory or PYTHONPATH not set

**Solution**:
```bash
# Make sure you're in backend directory
cd /home/deuce/agriconnect_ai/backend

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Then run
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### ❌ Error: "No module named 'uvicorn'"
**Cause**: Virtual environment not activated or uvicorn not installed

**Solution**:
```bash
cd /home/deuce/agriconnect_ai/backend
source venv/bin/activate
pip install uvicorn[standard]
```

### ❌ Error: "Address already in use"
**Cause**: Port is already taken by another process

**Solution**:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### ❌ Using System Python Instead of Venv
**Cause**: Venv not activated or using system uvicorn

**Solution**:
```bash
# Always activate venv first
source venv/bin/activate

# Verify you're using venv Python
which python  # Should show: .../venv/bin/python

# Use python -m uvicorn (not just uvicorn)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Default Credentials

- **Username**: `walter`
- **Password**: `wale`

---

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

Or kill by port:
```bash
lsof -ti:8000 | xargs kill -9  # For port 8000
lsof -ti:8080 | xargs kill -9  # For port 8080
```

---

## Testing the Application

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Test Users Endpoint
```bash
curl http://localhost:8000/test-users
```

### Login (Get Token)
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=walter&password=wale"
```

---

## Current Status

✅ **Server Running**: Port 8080
✅ **Dependencies**: Installed
✅ **Virtual Environment**: Configured
✅ **All Features**: Ready

Enjoy your AgriConnect AI platform! 🚀

