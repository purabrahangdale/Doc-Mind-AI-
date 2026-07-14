from fastapi import APIRouter

# Initialize the router for health check and general system status endpoints
router = APIRouter()

@router.get("/")
async def root():
    """
    Root endpoint serving as a welcome message and basic health check.
    Returns a welcome message indicating backend status.
    """
    return {
        "message": "Welcome to DocMind AI API"
    }
