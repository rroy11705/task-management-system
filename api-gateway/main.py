"""
API Gateway service for the Task Management System.
Acts as the entry point for all client requests, routing them to appropriate microservices.
"""

import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import httpx

from middleware import extract_tenant, verify_jwt_token

# Initialize FastAPI app
app = FastAPI(title="Task Management System - API Gateway")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
TENANT_RESOLVER_SERVICE_URL = os.getenv("TENANT_RESOLVER_SERVICE_URL", "http://localhost:8001")
USER_MANAGEMENT_SERVICE_URL = os.getenv("USER_MANAGEMENT_SERVICE_URL", "http://localhost:8002")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", "http://localhost:8003")
URL_SHORTENER_SERVICE_URL = os.getenv("URL_SHORTENER_SERVICE_URL", "http://localhost:8004")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8005")

# Async HTTP client
http_client = httpx.AsyncClient()

@app.get("/")
async def root():
    return {"message": "Welcome to Task Management System API Gateway"}

# Auth endpoints - proxy to User Management Service
@app.post("/auth/login")
async def login(request: Request):
    # TODO: Proxy request to User Management Service
    pass

@app.post("/auth/register")
async def register(request: Request):
    # TODO: Proxy request to User Management Service
    pass

# Project endpoints - proxy to Project Service
@app.get("/projects", dependencies=[Depends(verify_jwt_token), Depends(extract_tenant)])
async def get_projects(request: Request):
    # TODO: Proxy request to Project Service based on tenant
    pass

@app.post("/projects", dependencies=[Depends(verify_jwt_token), Depends(extract_tenant)])
async def create_project(request: Request):
    # TODO: Proxy request to Project Service based on tenant
    pass

# Task endpoints - proxy to Project Service
@app.get("/tasks", dependencies=[Depends(verify_jwt_token), Depends(extract_tenant)])
async def get_tasks(request: Request):
    # TODO: Proxy request to Project Service based on tenant
    pass

@app.post("/tasks", dependencies=[Depends(verify_jwt_token), Depends(extract_tenant)])
async def create_task(request: Request):
    # TODO: Proxy request to Project Service based on tenant
    pass

# URL Shortener endpoints - proxy to URL Shortener Service
@app.post("/url/shorten", dependencies=[Depends(verify_jwt_token)])
async def shorten_url(request: Request):
    # TODO: Proxy request to URL Shortener Service
    pass

@app.get("/url/{short_code}")
async def redirect_url(short_code: str):
    # TODO: Proxy request to URL Shortener Service
    pass

# Analytics endpoints - proxy to Analytics Service
@app.get("/analytics", dependencies=[Depends(verify_jwt_token)])
async def get_analytics(request: Request):
    # TODO: Proxy request to Analytics Service
    pass

@app.on_event("startup")
async def startup_event():
    # TODO: Initialize any startup tasks
    pass

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()