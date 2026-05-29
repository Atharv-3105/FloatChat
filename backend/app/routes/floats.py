from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession 
from app.database import get_db
from app.schemas.query import FloatLocation


router = APIRouter(prefix = "/floats", tags = ["Floats"])

@router.get("")
async def get_float_location(limit: int = Query(100, ge = 1, le=1000),
                             db: AsyncSession = Depends(get_db)):
    
    query = text("""
                 SELECT float_id, latitude, longitude, MAX(date) as last_date
                 FROM argo_data
                 WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                 GROUP BY float_id
                 ORDER BY last_date DESC 
                 LIMIT :limit
                 """)
    
    result = await db.execute(query, {"limit": limit})
    rows = result.fetchall()
    
    return [
        FloatLocation(
            float_id=row.float_id,
            latitude = row.latitude,
            longitude = row.longitude,
            last_date = row.last_date
        )
        for row in rows
    ]
    
    