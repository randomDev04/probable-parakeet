from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session


app = FastAPI(title="FastAPI with SQLAlchemy", description="A simple FastAPI application with SQLAlchemy integration.", version="1.0.0")

@app.get("/health", summary="Health Check", description="Check the health of the application.")
def health_check():
    return {"status": "healthy"}