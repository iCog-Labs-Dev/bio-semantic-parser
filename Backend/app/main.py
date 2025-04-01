from fastapi import FastAPI
from app.routes import router  # Import the router from routes.py

app = FastAPI(
    title="FastAPI App",
    description="A simple FastAPI service",
    version="1.0"
)

# Include the routes
app.include_router(router)

