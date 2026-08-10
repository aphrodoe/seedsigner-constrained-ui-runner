#!/bin/bash
set -e

echo "=========================================="
echo " SeedSigner Constrained UI Runner Setup   "
echo "=========================================="

echo "[1/3] Initializing git submodules..."
git submodule update --init --recursive

echo "[2/3] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "[3/3] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Pillow 10.3.0 fails to compile from source on Python 3.13 (Pi Zero).
# Relax the version requirement to allow downloading a pre-compiled wheel.
sed -i 's/Pillow==10.3.0/Pillow>=10.3.0/' vendor/seedsigner/requirements.txt
pip install -r vendor/seedsigner/requirements.txt
git -C vendor/seedsigner checkout requirements.txt

# Install Constrained UI Runner's own hardware dependencies
pip install -r requirements.txt

pip install embit urtypes==1.0.1

echo ""
echo "=========================================="
echo " Setup Complete! "
echo "=========================================="
echo "To run the full SeedSigner OS, execute:"
echo ""
echo "    source venv/bin/activate"
echo "    python3 run_seedsigner.py"
echo ""
