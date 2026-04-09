from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, ArgoData, QueryCache
import os 
from dotenv import load_dotenv 

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_async_engine(DATABASE_URL, echo = False)

async_session = sessionmaker(bind = engine, 
                             class_=AsyncSession, 
                             expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
        
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)