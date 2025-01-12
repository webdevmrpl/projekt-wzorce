#!/bin/sh

set -e

cd /app/src

echo "------------- Creating virtual environment..."
python3 -m venv ./venv
. ./venv/bin/activate

echo "------------- Installing Python dependencies..."
pip install -r requirements.txt
