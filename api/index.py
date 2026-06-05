"""
Vercel Serverless Function Entry Point for FastAPI
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import app
from mangum import Mangum

# Create the Mangum handler for Vercel
handler = Mangum(app, lifespan="off")
