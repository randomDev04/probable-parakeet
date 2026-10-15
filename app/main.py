from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers import auth

@asynccontextmanager
async def lifespan(app:FastAPI):
    """Lifespan context manager for FastAPI application."""
    Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
    # Startup code can be added here
    yield
    # Shutdown code can be added here


app = FastAPI(title="FastAPI with SQLAlchemy", description="A simple FastAPI application with SQLAlchemy integration.", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)

@app.get("/health", summary="Health Check", description="Check the health of the application.")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}

