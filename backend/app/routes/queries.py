from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/queries", tags=["Queries"])


@router.post("", response_model=QueryResponse)
async def process_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Processes a user query and returns the complete response.
    """
    service = QueryService(db)
    
    response = await service.process_query(
        user_query=request.query,
        model_name=request.model,
        max_results=request.max_results
    )
    
    return response


@router.get("/suggestions")
async def get_suggestions():
    ''' 
        Some examples of query suggestions
    '''
    return {
        "suggestions": [
            "Show temperature profile at 500m depth",
            "What floats are near Mumbai",
            "Average salinity in Bay of Bengal",
            "Compare temperature between floats"
        ]
    }