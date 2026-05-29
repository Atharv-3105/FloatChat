from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from contextlib import asynccontextmanager
from app.routes import health_router, queries_router, floats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    
    
app = FastAPI(
    title = settings.APP_NAME,
    version = settings.APP_VERSION,
    docs_url = "/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(health_router, prefix = "/api/v1")
app.include_router(queries_router, prefix = "/api/v1")
app.include_router(floats_router, prefix = "/api/v1")

    
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }