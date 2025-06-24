#!/bin/bash

# Build script para Railway
echo "🔄 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"
echo "📦 Backend ready to start with uvicorn" 