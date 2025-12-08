# Fixing distutils Error for Python 3.12

## Problem
Python 3.12 removed the `distutils` module, which some packages (like `prophet`, `geopandas`) still require during installation.

## Solutions

### Option 1: Install setuptools (Recommended)
```bash
pip install setuptools
```

This provides a replacement for distutils.

### Option 2: Use Python 3.11 or earlier
If you need packages that require distutils, consider using Python 3.11:
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 3: Install minimal requirements
Use the minimal requirements file that excludes problematic packages:
```bash
pip install -r requirements-minimal.txt
```

### Option 4: Install problematic packages separately
Some packages can be installed with workarounds:
```bash
# Install setuptools first
pip install setuptools

# Then try installing problematic packages
pip install prophet --no-build-isolation
pip install geopandas --no-build-isolation
```

## Current Status
The core application should work without these optional packages:
- ✅ FastAPI, Uvicorn (core web framework)
- ✅ SQLAlchemy (database)
- ✅ Pydantic (data validation)
- ✅ Basic ML packages (numpy, pandas)

Optional packages (can be added later):
- ⚠️ TensorFlow (for advanced ML)
- ⚠️ Prophet (for time-series forecasting - we have a simple alternative)
- ⚠️ GeoPandas (for advanced geospatial - we use geopy instead)

## Quick Fix
```bash
cd backend
source venv/bin/activate
pip install setuptools
pip install -r requirements-minimal.txt
```

