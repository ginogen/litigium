#!/usr/bin/env python3
"""
Script de entrada para Railway deployment
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        log_level="info"
    ) 