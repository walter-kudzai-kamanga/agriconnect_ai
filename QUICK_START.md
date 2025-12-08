# Quick Start Guide

## Starting the Application

### Option 1: From Project Root
```bash
cd /home/deuce/agriconnect_ai
./start_all.sh
```

### Option 2: From Backend Directory
```bash
cd /home/deuce/agriconnect_ai/backend
./start_all.sh
```

### Option 3: Manual Start (if script doesn't work)
```bash
cd /home/deuce/agriconnect_ai/backend

# Activate virtual environment (if exists)
source venv/bin/activate  # or: source ../venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the main app
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Troubleshooting

### Error: "No module named 'app'"
**Solution**: Make sure you're running from the `backend` directory and PYTHONPATH is set:
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Error: "No module named 'fastapi'"
**Solution**: Install dependencies or activate virtual environment:
```bash
# If venv exists
source venv/bin/activate
pip install -r requirements.txt

# Or install system-wide
pip3 install -r requirements.txt
```

### Error: "bash: ./start_all.sh: No such file or directory"
**Solution**: Make sure you're in the correct directory:
```bash
# Check current directory
pwd

# Should be either:
# /home/deuce/agriconnect_ai (project root)
# /home/deuce/agriconnect_ai/backend (backend directory)

# Then run:
cd backend  # if in project root
./start_all.sh
```

## Accessing the Dashboard

Once started, open your browser to:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Default Credentials

- Username: `walter`
- Password: `wale`

## Stopping the Application

```bash
cd backend
./stop_all.sh
```

Or manually kill processes:
```bash
pkill -f "uvicorn app.main"
pkill -f "python.*main.py"
```

