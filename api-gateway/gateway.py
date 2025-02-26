from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# Define backend services (mock microservices)
SERVICES = {
    "user": "http://127.0.0.1:8001",
    "order": "http://127.0.0.1:8002",
}


async def proxy_request(service_name: str, request: Request):
    """Forward the request to the appropriate microservice"""
    if service_name not in SERVICES:
        return {"error": "Service not found"}

    # Construct the full URL
    target_url = f"{SERVICES[service_name]}{request.url.path}"
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            params=request.query_params,
            headers=request.headers.raw,
            json=await request.json() if request.method in ["POST", "PUT"] else None,
        )
        return response.json()


@app.get("/{service}/{path:path}")
@app.post("/{service}/{path:path}")
@app.put("/{service}/{path:path}")
@app.delete("/{service}/{path:path}")
async def route_request(service: str, path: str, request: Request):
    """Route requests to the appropriate microservice"""
    return await proxy_request(service, request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gateway:app", host="0.0.0.0", port=8000, reload=True)
