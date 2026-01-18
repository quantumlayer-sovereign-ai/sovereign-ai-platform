"""
HIGH-QUALITY FASTAPI PROJECT TEMPLATE
=====================================
This is a complete, production-ready FastAPI project structure.
Use this as a reference for generating new projects.

Project Structure:
app/
├── __init__.py
├── main.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── models/
│   ├── __init__.py
│   ├── database.py
│   └── schemas.py
├── services/
│   ├── __init__.py
│   └── base_service.py
├── routers/
│   ├── __init__.py
│   └── api.py
└── utils/
    ├── __init__.py
    └── helpers.py
requirements.txt
.env.example
"""

# ============================================================================
# FILE: app/config/settings.py
# ============================================================================
"""Application settings using Pydantic v2."""
from functools import lru_cache
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    APP_NAME: str = "FastAPI Application"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Model configuration for Pydantic v2
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


# ============================================================================
# FILE: app/models/database.py
# ============================================================================
"""Database configuration with async SQLAlchemy."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ============================================================================
# FILE: app/models/schemas.py
# ============================================================================
"""Pydantic schemas for request/response validation."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Pydantic v2 (replaces orm_mode)
        str_strip_whitespace=True,
    )


class HealthResponse(BaseSchema):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseSchema):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: str


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    items: list
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# FILE: app/services/base_service.py
# ============================================================================
"""Base service class with common functionality."""
from typing import Generic, TypeVar, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseService(Generic[ModelType]):
    """Base service with CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
            await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            return True
        return False


# ============================================================================
# FILE: app/routers/api.py
# ============================================================================
"""API router with endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.database import get_db
from app.models.schemas import HealthResponse, ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )


@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an item by ID."""
    # Example endpoint - replace with actual service call
    if item_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return {"id": item_id, "name": f"Item {item_id}"}


# ============================================================================
# FILE: app/main.py
# ============================================================================
"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.models.database import init_db
from app.routers.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the API", "docs": "/docs"}


# ============================================================================
# FILE: requirements.txt
# ============================================================================
"""
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
python-dotenv>=1.0.0
"""


# ============================================================================
# FILE: .env.example
# ============================================================================
"""
APP_NAME=My FastAPI App
APP_VERSION=1.0.0
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./app.db
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
