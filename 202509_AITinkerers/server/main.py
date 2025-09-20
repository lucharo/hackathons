from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import meal_planning, mcp

app = FastAPI(
    title="Meal Coach API", 
    version="1.0.0",
    description="API for meal planning and grocery shopping via MCP integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meal_planning.router)
app.include_router(mcp.router)

@app.get("/")
async def root():
    return {
        "message": "Meal Coach API",
        "version": "1.0.0",
        "endpoints": {
            "meal_planning": "/meal-planning",
            "mcp": "/mcp",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "meal-coach-api",
        "components": {
            "meal_planning": "available",
            "mcp": "available"
        }
    }
