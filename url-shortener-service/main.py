"""
URL Shortener Service for the Task Management System.
Creates and manages shortened URLs for sharing tasks.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database import get_db, init_db
from models import URLModel
from schemas import URLCreate, URL, URLAccess
from services import url_service
from events import rabbitmq_client
from auth import get_current_user

# Initialize FastAPI app
app = FastAPI(title="Task Management System - URL Shortener Service")

# Initialize database
init_db()

@app.get("/")
async def root():
    return {"message": "URL Shortener Service"}

@app.post("/urls", response_model=URL)
async def create_shortened_url(
    url: URLCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a shortened URL.
    """
    # TODO: Implement URL shortening logic
    # 1. Generate shortened URL
    # 2. Store URL mapping in database
    # 3. Publish URLCreated event
    pass

@app.get("/urls/{short_code}", response_model=URL)
async def get_url(
    short_code: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get URL details by short code.
    """
    # TODO: Implement URL retrieval logic
    # 1. Get URL from database by short code
    # 2. Check if URL exists and user has access
    pass

@app.get("/r/{short_code}")
async def redirect_url(
    short_code: str,
    request: Request,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Redirect to original URL.
    """
    # TODO: Implement URL redirection logic
    # 1. Get URL from database by short code
    # 2. Check if URL exists and is not expired
    # 3. Verify password if required
    # 4. Publish URLAccessed event
    # 5. Return redirection response
    pass

@app.on_event("startup")
async def startup_event():
    await rabbitmq_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await rabbitmq_client.close()