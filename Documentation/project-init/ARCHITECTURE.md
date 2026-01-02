# Software Architecture Document
## Inventory Management REST API - Comercial Comarapa

**Document Version:** 1.0  
**Created:** January 2, 2026  
**Related PRD:** PRD-inventory-management-api.md  

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [System Context](#2-system-context)
3. [Technology Stack](#3-technology-stack)
4. [Application Layers](#4-application-layers)
5. [Project Structure](#5-project-structure)
6. [Component Details](#6-component-details)
7. [Data Flow](#7-data-flow)
8. [Database Architecture](#8-database-architecture)
9. [Design Patterns](#9-design-patterns)
10. [Error Handling Strategy](#10-error-handling-strategy)
11. [Configuration Management](#11-configuration-management)
12. [Security Architecture](#12-security-architecture)

---

## 1. Architecture Overview

The system follows a **Layered Architecture** pattern with clear separation of concerns. This design promotes maintainability, testability, and scalability.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│              (Frontend Apps, Mobile, External APIs)             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                       API LAYER (FastAPI)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │  Products   │ │ Categories  │ │  Inventory  │ │   Sales   │  │
│  │   Router    │ │   Router    │ │   Router    │ │  Router   │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ Dependency Injection
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │  Product    │ │  Category   │ │  Inventory  │ │   Sale    │  │
│  │  Service    │ │  Service    │ │  Service    │ │  Service  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ Repository Pattern
┌─────────────────────────────────────────────────────────────────┐
│                     REPOSITORY LAYER                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │  Product    │ │  Category   │ │  Inventory  │ │   Sale    │  │
│  │   Repo      │ │    Repo     │ │    Repo     │ │   Repo    │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ Supabase Client
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                             │
│                   Supabase (PostgreSQL)                         │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌──────────────┐   │
│  │ products │ │categories│ │inv_movements  │ │ sales/items  │   │
│  └──────────┘ └──────────┘ └───────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. System Context

### Context Diagram (C4 Level 1)

```
                    ┌─────────────────┐
                    │   Store Staff   │
                    │    (Actor)      │
                    └────────┬────────┘
                             │ Uses
                             ▼
                    ┌─────────────────┐
                    │  Frontend App   │
                    │   (Future)      │
                    └────────┬────────┘
                             │ REST API
                             ▼
┌────────────────────────────────────────────────────────────┐
│                                                            │
│              Comercial Comarapa Backend API                │
│                                                            │
│  • Manages product catalog (~1000 items)                   │
│  • Controls inventory movements                            │
│  • Registers sales transactions                            │
│  • Provides low stock alerts                               │
│                                                            │
└────────────────────────────────────────────────────────────┘
                             │
                             │ PostgreSQL Protocol
                             ▼
                    ┌─────────────────┐
                    │    Supabase     │
                    │  (PostgreSQL)   │
                    │                 │
                    │  Cloud Database │
                    └─────────────────┘
```

### Container Diagram (C4 Level 2)

```
┌──────────────────────────────────────────────────────────────────┐
│                     Comercial Comarapa System                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Backend API Container                  │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │  FastAPI   │  │  Pydantic  │  │  Supabase Client   │  │   │
│  │  │  Framework │  │  Models    │  │                    │  │   │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │  Uvicorn   │  │   Ruff     │  │   python-dotenv    │  │   │
│  │  │  Server    │  │  Linter    │  │                    │  │   │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Supabase Platform                      │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │ PostgreSQL │  │    Auth    │  │   Row Level Sec.   │  │   │
│  │  │  Database  │  │  (Future)  │  │     (Future)       │  │   │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Runtime Environment

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.14 | Runtime environment |
| Hatch | Latest | Project & dependency management |
| Uvicorn | 0.27+ | ASGI server |

### Core Framework & Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.109+ | Web framework |
| Pydantic | 2.5+ | Data validation & serialization |
| pydantic-settings | 2.1+ | Configuration management |
| supabase-py | 2.3+ | Supabase client |
| httpx | 0.26+ | HTTP client (async) |
| python-dotenv | 1.0+ | Environment variables |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Ruff | 0.1+ | Linting & formatting |
| pytest | 7.4+ | Testing framework |
| pytest-asyncio | 0.23+ | Async test support |
| pytest-cov | 4.1+ | Code coverage |

---

## 4. Application Layers

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│  Responsibilities:                                          │
│  • HTTP request/response handling                           │
│  • Request validation (via Pydantic)                        │
│  • Route definitions                                        │
│  • OpenAPI documentation                                    │
│  • Dependency injection setup                               │
│                                                             │
│  Files: api/v1/*.py                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                            │
│  Responsibilities:                                          │
│  • Business logic implementation                            │
│  • Transaction coordination                                 │
│  • Cross-entity operations                                  │
│  • Business rule validation                                 │
│  • Event orchestration                                      │
│                                                             │
│  Files: services/*.py                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                          │
│  Responsibilities:                                          │
│  • Data access abstraction                                  │
│  • CRUD operations                                          │
│  • Query building                                           │
│  • Database-specific logic                                  │
│                                                             │
│  Files: db/repositories/*.py                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MODEL LAYER                             │
│  Responsibilities:                                          │
│  • Data transfer objects (DTOs)                             │
│  • Request/Response schemas                                 │
│  • Validation rules                                         │
│  • Type definitions                                         │
│                                                             │
│  Files: models/*.py                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Project Structure

```
BackEnd-CC/
│
├── pyproject.toml                 # Hatch configuration & dependencies
├── README.md                      # Project documentation
├── .env.example                   # Environment template
├── .env                           # Local environment (git-ignored)
├── .gitignore                     # Git ignore rules
│
├── src/
│   └── comercial_comarapa/        # Main application package
│       │
│       ├── __init__.py            # Package initialization
│       ├── main.py                # FastAPI app factory & startup
│       ├── config.py              # Settings class (pydantic-settings)
│       │
│       ├── api/                   # API Layer
│       │   ├── __init__.py
│       │   ├── deps.py            # Shared dependencies
│       │   │
│       │   └── v1/                # API Version 1
│       │       ├── __init__.py
│       │       ├── router.py      # Main router aggregator
│       │       ├── products.py    # Product endpoints
│       │       ├── categories.py  # Category endpoints
│       │       ├── inventory.py   # Inventory endpoints
│       │       └── sales.py       # Sales endpoints
│       │
│       ├── models/                # Pydantic Schemas
│       │   ├── __init__.py
│       │   ├── common.py          # Shared models (pagination, responses)
│       │   ├── product.py         # Product schemas
│       │   ├── category.py        # Category schemas
│       │   ├── inventory.py       # Inventory movement schemas
│       │   └── sale.py            # Sale schemas
│       │
│       ├── services/              # Business Logic Layer
│       │   ├── __init__.py
│       │   ├── product_service.py
│       │   ├── category_service.py
│       │   ├── inventory_service.py
│       │   └── sale_service.py
│       │
│       ├── db/                    # Database Layer
│       │   ├── __init__.py
│       │   ├── supabase.py        # Supabase client singleton
│       │   │
│       │   └── repositories/      # Repository Pattern
│       │       ├── __init__.py
│       │       ├── base.py        # Base repository class
│       │       ├── product_repo.py
│       │       ├── category_repo.py
│       │       ├── inventory_repo.py
│       │       └── sale_repo.py
│       │
│       └── core/                  # Core Utilities
│           ├── __init__.py
│           ├── exceptions.py      # Custom exception classes
│           ├── responses.py       # Standard response builders
│           └── logging.py         # Logging configuration
│
├── tests/                         # Test Suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_products.py
│   ├── test_categories.py
│   ├── test_inventory.py
│   └── test_sales.py
│
└── Documentation/                 # Project Documentation
    ├── project-init/
    │   ├── PRD-inventory-management-api.md
    │   └── ARCHITECTURE.md        # This document
    ├── database/
    │   └── schema.sql
    └── api/
        └── examples.md
```

---

## 6. Component Details

### 6.1 Main Application (`main.py`)

```python
# Responsibilities:
# - FastAPI application instance creation
# - Router registration
# - Middleware configuration
# - Startup/shutdown events
# - CORS configuration

from fastapi import FastAPI
from comercial_comarapa.api.v1.router import api_router
from comercial_comarapa.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    
    return app
```

### 6.2 Configuration (`config.py`)

```python
# Responsibilities:
# - Load environment variables
# - Validate configuration
# - Provide typed settings access

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "comercial-comarapa-api"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
```

### 6.3 API Router Structure

```
api/v1/router.py
       │
       ├── products.py     → /api/v1/products/*
       ├── categories.py   → /api/v1/categories/*
       ├── inventory.py    → /api/v1/inventory/*
       └── sales.py        → /api/v1/sales/*
```

### 6.4 Model Schemas Organization

```
models/
├── common.py
│   ├── PaginationParams    # Query params for pagination
│   ├── PaginatedResponse   # Generic paginated response
│   ├── APIResponse         # Standard API response wrapper
│   └── ErrorResponse       # Error response format
│
├── product.py
│   ├── ProductBase         # Shared fields
│   ├── ProductCreate       # Create request
│   ├── ProductUpdate       # Update request (partial)
│   ├── ProductResponse     # API response
│   └── ProductListResponse # List with pagination
│
├── category.py
│   ├── CategoryBase
│   ├── CategoryCreate
│   ├── CategoryUpdate
│   └── CategoryResponse
│
├── inventory.py
│   ├── MovementType        # Enum: ENTRY, EXIT, ADJUSTMENT
│   ├── MovementReason      # Enum: PURCHASE, SALE, etc.
│   ├── StockEntryRequest
│   ├── StockExitRequest
│   ├── StockAdjustmentRequest
│   └── MovementResponse
│
└── sale.py
    ├── SaleStatus          # Enum: COMPLETED, CANCELLED
    ├── SaleItemCreate
    ├── SaleCreate
    ├── SaleItemResponse
    ├── SaleResponse
    └── DailySummaryResponse
```

### 6.5 Service Layer Pattern

```python
# services/product_service.py

class ProductService:
    """
    Business logic for product operations.
    Coordinates between API layer and repository layer.
    """
    
    def __init__(self, product_repo: ProductRepository):
        self.repo = product_repo
    
    async def create_product(self, data: ProductCreate) -> Product:
        # Validate business rules
        await self._validate_unique_sku(data.sku)
        
        # Create product
        return await self.repo.create(data)
    
    async def get_low_stock_products(self) -> list[Product]:
        # Business logic: products where current_stock <= min_stock_level
        return await self.repo.find_low_stock()
    
    async def _validate_unique_sku(self, sku: str) -> None:
        existing = await self.repo.find_by_sku(sku)
        if existing:
            raise DuplicateSKUError(sku)
```

### 6.6 Repository Layer Pattern

```python
# db/repositories/base.py

class BaseRepository[T]:
    """
    Generic base repository with common CRUD operations.
    """
    
    def __init__(self, client: SupabaseClient, table_name: str):
        self.client = client
        self.table = table_name
    
    async def find_by_id(self, id: UUID) -> T | None:
        response = self.client.table(self.table).select("*").eq("id", str(id)).single().execute()
        return response.data
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        response = self.client.table(self.table).select("*").range(offset, offset + limit - 1).execute()
        return response.data
    
    async def create(self, data: dict) -> T:
        response = self.client.table(self.table).insert(data).execute()
        return response.data[0]
    
    async def update(self, id: UUID, data: dict) -> T:
        response = self.client.table(self.table).update(data).eq("id", str(id)).execute()
        return response.data[0]
    
    async def delete(self, id: UUID) -> bool:
        self.client.table(self.table).delete().eq("id", str(id)).execute()
        return True
```

---

## 7. Data Flow

### 7.1 Create Sale Flow

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Client  │────▶│ Sales Router │────▶│SaleService  │────▶│  SaleRepo    │
└──────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                              │
                                              │ For each item
                                              ▼
                                      ┌─────────────────┐
                                      │InventoryService │
                                      └─────────────────┘
                                              │
                                              ▼
                                      ┌─────────────────┐
                                      │  InventoryRepo  │
                                      └─────────────────┘
                                              │
                                              ▼
                                      ┌─────────────────┐
                                      │  ProductRepo    │
                                      │ (update stock)  │
                                      └─────────────────┘
```

**Sequence:**

```
1. Client POST /api/v1/sales
   └─▶ SaleCreate { items: [...], discount: 0 }

2. Sales Router
   └─▶ Validates request body (Pydantic)
   └─▶ Calls SaleService.create_sale()

3. SaleService.create_sale()
   └─▶ For each sale item:
       ├─▶ Validate product exists
       ├─▶ Check sufficient stock
       └─▶ Calculate line subtotal
   └─▶ Calculate sale totals
   └─▶ Call SaleRepo.create()
   └─▶ For each sale item:
       └─▶ InventoryService.register_exit()
           └─▶ Update product.current_stock
           └─▶ Create inventory_movement record

4. Return SaleResponse to client
```

### 7.2 Request/Response Flow

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Middleware                       │
│  • CORS handling                                            │
│  • Request logging (optional)                               │
│  • Error catching                                           │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pydantic Validation                      │
│  • Request body parsing                                     │
│  • Type coercion                                            │
│  • Validation errors (422)                                  │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Dependency Injection                      │
│  • Get Supabase client                                      │
│  • Instantiate repositories                                 │
│  • Instantiate services                                     │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Route Handler                           │
│  • Execute business logic                                   │
│  • Build response                                           │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
HTTP Response (JSON)
```

---

## 8. Database Architecture

### 8.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   categories    │       │    products     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◀──┐   │ id (PK)         │
│ name            │   │   │ sku             │
│ description     │   └───│ category_id(FK) │
│ created_at      │       │ name            │
└─────────────────┘       │ description     │
                          │ unit_price      │
                          │ cost_price      │
                          │ current_stock   │
                          │ min_stock_level │
                          │ is_active       │
                          │ created_at      │
                          │ updated_at      │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌─────────────────────┐       ┌─────────────────┐
        │ inventory_movements │       │   sale_items    │
        ├─────────────────────┤       ├─────────────────┤
        │ id (PK)             │       │ id (PK)         │
        │ product_id (FK)     │       │ sale_id (FK)    │
        │ movement_type       │       │ product_id (FK) │
        │ quantity            │       │ quantity        │
        │ reason              │       │ unit_price      │
        │ reference_id        │──┐    │ discount        │
        │ notes               │  │    │ subtotal        │
        │ previous_stock      │  │    └────────┬────────┘
        │ new_stock           │  │             │
        │ created_at          │  │             │
        │ created_by          │  │             ▼
        └─────────────────────┘  │    ┌─────────────────┐
                                 │    │     sales       │
                                 │    ├─────────────────┤
                                 │    │ id (PK)         │
                                 └───▶│ sale_number     │
                                      │ sale_date       │
                                      │ subtotal        │
                                      │ discount        │
                                      │ tax             │
                                      │ total           │
                                      │ status          │
                                      │ notes           │
                                      │ created_at      │
                                      │ created_by      │
                                      └─────────────────┘
```

### 8.2 Indexes Strategy

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| products | idx_products_sku | sku | SKU lookups |
| products | idx_products_name | name | Name search |
| products | idx_products_category | category_id | Category filtering |
| products | idx_products_low_stock | current_stock, min_stock_level | Low stock alerts |
| inventory_movements | idx_movements_product | product_id | Movement history |
| inventory_movements | idx_movements_date | created_at DESC | Recent movements |
| sales | idx_sales_date | sale_date DESC | Date filtering |
| sales | idx_sales_number | sale_number | Invoice lookup |
| sale_items | idx_sale_items_sale | sale_id | Sale details |

---

## 9. Design Patterns

### 9.1 Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Repository** | `db/repositories/` | Abstract data access |
| **Service Layer** | `services/` | Encapsulate business logic |
| **Dependency Injection** | `api/deps.py` | Decouple components |
| **Factory** | `main.py` | Create FastAPI app |
| **DTO (Data Transfer Object)** | `models/` | Request/Response schemas |
| **Singleton** | `db/supabase.py` | Single DB client instance |

### 9.2 Dependency Injection Flow

```python
# api/deps.py

from functools import lru_cache
from comercial_comarapa.db.supabase import get_supabase_client
from comercial_comarapa.db.repositories import ProductRepository
from comercial_comarapa.services import ProductService

@lru_cache
def get_supabase():
    """Singleton Supabase client."""
    return get_supabase_client()

def get_product_repo(client = Depends(get_supabase)):
    """Factory for ProductRepository."""
    return ProductRepository(client)

def get_product_service(repo = Depends(get_product_repo)):
    """Factory for ProductService."""
    return ProductService(repo)

# Usage in router:
@router.get("/products")
async def list_products(
    service: ProductService = Depends(get_product_service)
):
    return await service.get_all()
```

---

## 10. Error Handling Strategy

### 10.1 Exception Hierarchy

```
BaseAPIException (core/exceptions.py)
├── NotFoundError
│   ├── ProductNotFoundError
│   ├── CategoryNotFoundError
│   └── SaleNotFoundError
│
├── ValidationError
│   ├── DuplicateSKUError
│   ├── InvalidQuantityError
│   └── InsufficientStockError
│
├── ConflictError
│   └── CategoryHasProductsError
│
└── DatabaseError
    └── ConnectionError
```

### 10.2 Exception Handler

```python
# core/exceptions.py

class BaseAPIException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

class ProductNotFoundError(BaseAPIException):
    status_code = 404
    error_code = "PRODUCT_NOT_FOUND"
    
    def __init__(self, product_id: str):
        self.message = f"Product with ID {product_id} not found"

# main.py - Exception handler registration
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message
            }
        }
    )
```

---

## 11. Configuration Management

### 11.1 Environment Hierarchy

```
Production:   .env.production   (deployed)
Staging:      .env.staging      (pre-production)
Development:  .env              (local development)
Testing:      .env.test         (pytest)
```

### 11.2 Configuration Loading

```
1. Load from .env file (python-dotenv)
2. Override with system environment variables
3. Validate with Pydantic Settings
4. Access via settings singleton
```

### 11.3 Hatch Environment Configuration

```toml
# pyproject.toml

[tool.hatch.envs.default]
dependencies = [
    "ruff",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]

[tool.hatch.envs.default.scripts]
dev = "uvicorn comercial_comarapa.main:app --reload"
test = "pytest tests/ -v"
lint = "ruff check src/"
format = "ruff format src/"
check = ["lint", "test"]
```

---

## 12. Security Architecture

### 12.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      TRANSPORT LAYER                        │
│  • HTTPS (TLS 1.3)                                         │
│  • Certificate management                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                      │
│  • CORS configuration                                       │
│  • Input validation (Pydantic)                             │
│  • Rate limiting (future)                                   │
│  • JWT Authentication (optional)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                         │
│  • Supabase service role key (server-side only)            │
│  • Row Level Security (future)                             │
│  • Parameterized queries                                    │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 Credential Management

| Credential | Storage | Access |
|------------|---------|--------|
| SUPABASE_URL | .env file | Environment variable |
| SUPABASE_KEY | .env file | Environment variable |
| JWT_SECRET | .env file | Environment variable |

### 12.3 CORS Configuration

```python
# Allowed in development
CORS_ORIGINS = [
    "http://localhost:3000",    # React dev
    "http://localhost:5173",    # Vite dev
    "http://127.0.0.1:8000",    # API docs
]

# Production: restrict to actual frontend domain
CORS_ORIGINS = [
    "https://comercialcomarapa.com"
]
```

---

## Appendix A: Module Dependencies

```
comercial_comarapa/
│
├── main.py
│   └── imports: config, api.v1.router, core.exceptions
│
├── config.py
│   └── imports: pydantic_settings
│
├── api/v1/
│   ├── router.py
│   │   └── imports: products, categories, inventory, sales
│   │
│   └── products.py (example)
│       └── imports: models.product, services.product_service, api.deps
│
├── services/
│   └── product_service.py
│       └── imports: models.product, db.repositories.product_repo, core.exceptions
│
├── db/
│   ├── supabase.py
│   │   └── imports: supabase, config
│   │
│   └── repositories/product_repo.py
│       └── imports: db.repositories.base, models.product
│
├── models/
│   └── product.py
│       └── imports: pydantic, models.common
│
└── core/
    ├── exceptions.py
    │   └── imports: (none - base module)
    │
    └── responses.py
        └── imports: models.common
```

---

## Appendix B: Hatch Commands Reference

| Command | Description |
|---------|-------------|
| `hatch env create` | Create virtual environment |
| `hatch shell` | Activate environment |
| `hatch run dev` | Start development server |
| `hatch run test` | Run test suite |
| `hatch run lint` | Run Ruff linter |
| `hatch run format` | Format code with Ruff |
| `hatch run check` | Lint + Test |
| `hatch build` | Build package |

---

**Document Revision History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | - | Initial architecture document |

