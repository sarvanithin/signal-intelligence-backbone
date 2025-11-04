"""
FastAPI application for Signal Intelligence Backbone.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes.signals import router as signals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized. Ready to receive signals!")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Signal Intelligence Backbone",
    description="Backend service for coherence tracking in multi-agent environments",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(signals_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "signal-intelligence-backbone"}


@app.get("/")
async def root():
    """Root endpoint with API documentation link."""
    return {
        "message": "Signal Intelligence Backbone API",
        "docs": "/docs",
        "health": "/health"
    }
