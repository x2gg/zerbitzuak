from fastapi import APIRouter, Depends

from app.services.apisix import APISIXService
from app.schemas.consumer import ConsumerCreate, ConsumerResponse

router = APIRouter()


@router.post("/create-consumer", response_model=ConsumerResponse, include_in_schema=False)
async def create_consumer(
    consumer: ConsumerCreate,
    # current_user: dict = Depends(get_current_user)  # Uncomment to require authentication
) -> ConsumerResponse:
    """
    Create a new APISIX consumer.
    
    This endpoint creates only the consumer in APISIX, not a user in the database.
    Use the /users endpoint to create both.
    """
    apisix_service = APISIXService()
    
    if apisix_service.create_consumer(consumer):
        return ConsumerResponse(
            message=f"Consumer '{consumer.username}' created successfully",
            username=consumer.username
        )


@router.delete("/delete-consumer/{username}", include_in_schema=False)
async def delete_consumer(
    username: str,
    # current_user: dict = Depends(get_current_user)  # Uncomment to require authentication
) -> dict:
    """
    Delete an APISIX consumer.
    
    This only deletes the consumer from APISIX, not the user from the database.
    """
    apisix_service = APISIXService()
    
    if apisix_service.delete_consumer(username):
        return {"message": f"Consumer '{username}' deleted successfully"}