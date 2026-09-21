from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.router import api_router

app = FastAPI(title=settings.APP_NAME)

# Ensure tables exist if running without Alembic (dev convenience)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API router
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}
