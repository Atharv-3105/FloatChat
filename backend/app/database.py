from sqlalchemy import Column, Integer, String, Float, DateTime, Index, create_engine, text 
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

#Sync Engine for Scripts
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiosqlite", ""),
    connect_args = {"check_same_thread" : False}
)
SyncSession = sessionmaker(bind = sync_engine, class_=Session)

#Async Engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread":False}
)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


#======SQL Models==========
class ArgoData(Base):
    
    __tablename__ = "argo_data"
    
    id = Column(Integer, primary_key=True, index = True)
    float_id = Column(String(50), index = True, nullable = False)
    latitude = Column(Float, nullable = False)
    longitude = Column(Float, nullable = False)
    date = Column(DateTime, index = True)
    cycle_number = Column(Integer)
    pressure = Column(Float, nullable = False, index = True)
    temperature = Column(Float, nullable = False)
    salinity = Column(Float)
    
    __table_args__ = (
        Index('idx_float_id', 'float_id'),
        Index('idx_lat_lon', 'latitude', 'longitude'),
        Index('idx_pressure', 'pressure'),
    )
    
    def __repr__(self):
        return f"<ArgoData(float_id = {self.float_id}, temp = {self.temperature})>"
    

async def get_db():
    ''' 
        Get async database session 
    '''
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
def get_sync_db():
    return SyncSession()

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)