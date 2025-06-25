#!/usr/bin/env python3
"""
Simple entry point for Railway deployment
Starts the backend server from the project root
"""

import os
import sys
import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from backend.main
from backend.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting Legal Assistant AI Backend on port {port}")
    print(f"📂 Project root: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"🐍 Python path: {sys.path[:3]}")  # Show first 3 entries
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=False  # Disable access logs for Railway
    ) 