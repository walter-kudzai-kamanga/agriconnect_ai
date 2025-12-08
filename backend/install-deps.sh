#!/bin/bash

# Script to install dependencies with distutils fix for Python 3.12

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    PIP_CMD="pip"
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    PIP_CMD="pip"
else
    PIP_CMD="pip3"
fi

echo "Installing setuptools (fixes distutils issue)..."
$PIP_CMD install setuptools

echo ""
echo "Installing core dependencies..."
$PIP_CMD install -r requirements-minimal.txt

echo ""
echo "Attempting to install optional packages..."
echo "(Some may fail on Python 3.12 - that's OK)"

# Try optional packages one by one
for package in "scikit-learn==1.3.2" "redis==5.0.1" "geopy==2.3.0" "folium==0.15.1"; do
    echo "Trying $package..."
    $PIP_CMD install "$package" || echo "  Failed (non-critical)"
done

echo ""
echo "Installation complete!"
echo "Core functionality should work now."

