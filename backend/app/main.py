from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.database import check_db_connection

from fastapi.openapi.utils import get_openapi




# Create FastAPI app
app = FastAPI(
	title=settings.PROJECT_NAME,
	version=settings.VERSION,
	#openapi_url=f"{settings.API_V1_STR}/openapi.json"
	openapi_url="/openapi.json",
	docs_url="/docs",
	redoc_url="/redoc",	
    servers=[{"url": "/api"}]
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["servers"] = [{"url": "/api"}]
    
    # Schemas to hide from Swagger UI (but keep in the spec)
    schemas_to_hide = [
        "UserLogin", "Token", "User", "GenerateApiKeyResponse",
        "UserProfile", "ValidationError", "SendPasswordRecoveryRequest",
        "SendPasswordRecoveryResponse"
    ]
    
    # Mark schemas as hidden by adding x-internal extension
    # This keeps them in the spec but hides them from Swagger UI
    for schema_name in schemas_to_hide:
        if schema_name in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"][schema_name]["x-internal"] = True
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi



# Configure CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Configure appropriately for production
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/health", include_in_schema=False)
def health_check():
	"""Check the health of the API and database connection."""
	if not check_db_connection():
		raise HTTPException(status_code=503, detail="Database connection failed")
	
	return {
		"status": "healthy",
		"version": settings.VERSION,
		"database": "connected"
	}


@app.on_event("startup")
async def startup_event():
	"""Run on application startup."""
	print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
	print(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
	print(f"APISIX Admin: {settings.APISIX_ADMIN_URL}")
	
	# Check database connection
	if not check_db_connection():
		print("WARNING: Database connection failed on startup")



@app.on_event("shutdown")
async def shutdown_event():
	"""Run on application shutdown."""
	print(f"Shutting down {settings.PROJECT_NAME}")


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=4100)
