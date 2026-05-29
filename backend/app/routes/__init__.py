from app.routes.health import router as health_router
from app.routes.queries import router as queries_router
from app.routes.floats import router as floats_router

__all__ = ["health_router", "queries_router", "floats_router"]

