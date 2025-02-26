# Task Management System - Microservices Architecture

A comprehensive task management system with Kanban board functionality, implemented as a microservices architecture using FastAPI and Docker.

## Project Overview

This system provides:
- Task management with Kanban board functionality
- Multi-tenant isolation with separate databases per tenant
- Task sharing via URL shortening with expiration and password protection
- Analytics for task management and URL usage

## Architecture

The system follows a microservices architecture with:
- API Gateway
- Tenant Resolver Service
- User Management Service
- Project Service
- URL Shortener Service
- Analytics Service

Each service is deployed as an independent Docker container, orchestrated with Docker Compose.

## Technology Stack

- **Backend**: FastAPI (Python)
- **Databases**: PostgreSQL (relational data, tenant-specific), MongoDB (analytics)
- **Message Broker**: RabbitMQ for event-driven communication
- **Containerization**: Docker and Docker Compose
- **Authentication**: JWT-based auth with role-based access control

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.9+

### Setup Instructions
1. Clone the repository
2. Run `docker-compose up -d`
3. Access the API at `http://localhost:8000`

## Services

### API Gateway
Entry point for all client requests, routes to appropriate microservices.

### Tenant Resolver Service
Manages organization subdomains and their corresponding database connections.

### User Management Service
Handles authentication, authorization, and user management.

### Project Service
Manages projects, tasks, and Kanban boards.

### URL Shortener Service
Creates and manages shortened URLs for sharing tasks.

### Analytics Service
Collects and processes analytics data for tasks and URL usage.

## Development Roadmap

See the detailed development roadmap in the project documentation.

## Contributing

Guidelines for contributing to the project will be added here.

## License

This project is licensed under [LICENSE] - see the LICENSE file for details.