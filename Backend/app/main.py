from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router  # Import the router from routes.py

app = FastAPI(
    title="FastAPI App",
    description="A simple FastAPI service",
    version="1.0"
)

# Allow CORS for frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(router)

