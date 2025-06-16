from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router  # assuming routes.py is in same directory
from fastapi.staticfiles import StaticFiles
import os
    
app = FastAPI(
    title="Pharmacy Price Comparison API",
    description="Compare product prices between PharmEasy, Apollo, and your own offers.",
    version="1.0.0"
)

# Allow frontend access (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Pharmacy Comparison API"}

#front-end acces
app.include_router(router, prefix="/api")
# Get absolute path to /app/front-end
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "front-end")

# Serve static files
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

