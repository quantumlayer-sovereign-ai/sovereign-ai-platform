"""
PYTHON IMPORTS QUICK REFERENCE
==============================
Use this reference to ensure correct imports in generated code.
"""

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================

# Type hints
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from collections.abc import AsyncGenerator, Generator, Sequence

# Data types
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from uuid import UUID, uuid4
from enum import Enum, auto

# Async
import asyncio
from contextlib import asynccontextmanager

# Other common
import json
import logging
import os
import re
from pathlib import Path
from functools import lru_cache, wraps


# ============================================================================
# PYDANTIC V2 IMPORTS
# ============================================================================

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    computed_field,
)
from pydantic_settings import BaseSettings


# ============================================================================
# FASTAPI IMPORTS
# ============================================================================

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Path as PathParam,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# ============================================================================
# SQLALCHEMY IMPORTS (Async)
# ============================================================================

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    select,
    update,
    delete,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ============================================================================
# COMMON PATTERNS
# ============================================================================

# Correct Pydantic v2 model
class ExampleSchema(BaseModel):
    """Example schema with proper Pydantic v2 syntax."""

    id: int
    name: str = Field(..., min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, ge=Decimal("0"))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )


# Correct Pydantic v2 settings
class ExampleSettings(BaseSettings):
    """Example settings with proper Pydantic v2 syntax."""

    app_name: str = "My App"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./app.db"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Correct SQLAlchemy async model
class ExampleModel(DeclarativeBase):
    """Example model with proper SQLAlchemy 2.0 syntax."""

    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
