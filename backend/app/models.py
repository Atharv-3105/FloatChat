from  sqlalchemy import Column,Integer, Float, String, DateTime 
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

#Structure in which ARGO Data will be stored
class ArgoData(Base):
    
    __tablename__ = "argo_data"
    
    id = Column(Integer, primary_key=True, index=True)
    float_id = Column(String, index=True, nullable=False) 
    latitude = Column(Float)
    longitude = Column(Float)
    date = Column(DateTime)
    cycle_number = Column(Integer)
    pressure = Column(Float)
    temperature = Column(Float)
    salinity = Column(Float)
    
    def __repr__(self):
        return f"<ArgoData(float_id = {self.float_id}, lat={self.latitude}, temp={self.temperature})>"
    
class QueryCache(Base):
    __tablename__ = "query_cache"
    
    id = Column(Integer, primary_key = True)
    query_text = Column(String, unique=True)
    response_json = Column(String)
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))
    model_used = Column(String)