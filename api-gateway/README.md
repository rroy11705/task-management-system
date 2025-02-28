# API Gateway Service

## Overview

The API Gateway service acts as the entry point for all client requests, routing them to appropriate microservices. It handles cross-cutting concerns like authentication, tenant resolution, rate limiting, and logging.

## Key Features

- **Request Routing**: Routes API requests to appropriate backend services
- **Authentication**: Extracts and validates JWT tokens
- **Tenant Resolution**: Extracts tenant information from subdomain or headers
- **Rate Limiting**: Implements basic rate limiting to prevent abuse
- **Logging**: Comprehensive request/response logging

## Technology Stack

- FastAPI framework
- JWT for authentication
- (Optional) Redis for distributed rate limiting

## Configuration

Configure the API Gateway using environment variables. Copy the `.env.example` file to `.env` and modify as needed:

```bash
cp .env.example .env
```

Key configuration options:

- `JWT_SECRET_KEY`: Secret key for JWT token validation
- `USER_MANAGEMENT_SERVICE_URL`: URL of the User Management Service
- `TENANT_RESOLVER_SERVICE_URL`: URL of the Tenant Resolver Service
- `RATE_LIMIT_PER_MINUTE`: Rate limit per client per minute

## Running Locally

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

### Using Docker

```bash
docker-compose up -d
```

## API Documentation

Once the service is running, access the OpenAPI documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `/health`: Health check endpoint
- `/api/users/*`: Proxies to User Management Service
- `/api/tenants/*`: Proxies to Tenant Resolver Service
- `/api/auth/*`: Authentication endpoints (no token required)

## Development

### Project Structure

```
.
├── config.py               # Configuration settings
├── main.py                 # FastAPI application entry point
├── middlewares/            # Middleware components
│   ├── logging_middleware.py
│   ├── rate_limit.py
│   └── tenant_resolver.py
└── utils/                  # Utility modules
    ├── jwt_utils.py
    └── service_registry.py
```

### Adding New Service Routes

To add routing for a new service, update the `main.py` file:

1. Register the service in the `startup_event` function
2. Add a new route group using `app.api_route`

Example:

```python
# Register service
service_registry.register_service("new-service", settings.NEW_SERVICE_URL)

# Add route
@app.api_route("/api/new-service/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def new_service_proxy(request: Request, path: str, user_info: Dict = Depends(get_token_header)):
    """Routes requests to the New Service."""
    return await proxy_request(request, "new-service", path)
```