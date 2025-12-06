from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import alerts, logs, stats, agent, logs, knowledge
from .demo_data import seed_demo_data
import os
import logging

# Create tables


app = FastAPI(
    title="SIEM Pilot API",
    description="Backend API for SecurityLLMLab SIEM Pilot",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)
app.include_router(logs.router)
app.include_router(stats.router)
app.include_router(agent.router)
app.include_router(knowledge.router)

@app.on_event("startup")
async def startup_event():
    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.warning(f"Could not create tables (DB might be unreachable): {e}")

    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
    if demo_mode:
        logging.info("Running in Demo Mode: Seeding data...")
        try:
            await seed_demo_data()
        except Exception as e:
            logging.error(f"Failed to seed demo data: {e}")

@app.get("/")
async def root():
    return {"message": "SIEM Pilot API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

