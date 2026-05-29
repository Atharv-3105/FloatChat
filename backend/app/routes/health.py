from fastapi import APIRouter
from datetime import datetime, timezone 
from app.config import settings

router = APIRouter(prefix="/health", tags = ["health"])

@router.get("")
async def health_check():
    
    return {
        "status" : "healthy",
        "service" : settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc)
    }
    
    