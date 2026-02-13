from fastapi import APIRouter

from app.api.v1 import auth, users, consumers, profiles, nlp

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(consumers.router, tags=["consumers"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(nlp.router, tags=["nlp"])