# Phase 1 Implementation Plan
## Backend REST API - Comercial Comarapa

**Document Version:** 1.1  
**Created:** January 2, 2026  
**Last Updated:** January 2, 2026  
**Status:** M0 Completed - Ready for M1  

---

## Progress Summary

```
Phase 0: Project Setup ████████████████████ 100% ✅
M0: Local Environment  ████████████████████ 100% ✅
M1: Core Models        ░░░░░░░░░░░░░░░░░░░░   0% ⏳ NEXT
M2: Categories API     ░░░░░░░░░░░░░░░░░░░░   0%
M3: Products API       ░░░░░░░░░░░░░░░░░░░░   0%
M4: Inventory API      ░░░░░░░░░░░░░░░░░░░░   0%
M5: Sales API          ░░░░░░░░░░░░░░░░░░░░   0%
M6: Error Handling     ░░░░░░░░░░░░░░░░░░░░   0%
M7: Documentation      ░░░░░░░░░░░░░░░░░░░░   0%
```

---

## Overview

This document provides a detailed, step-by-step implementation plan for Phase 1 of the Backend REST API. Tasks are organized by milestone and ordered by dependencies.

### Estimated Timeline

| Milestone | Estimated Effort | Dependencies | Status |
|-----------|------------------|--------------|--------|
| **M0: Local Environment** | 1-2 hours | None | ✅ Done |
| M1: Core Models | 2-3 hours | M0 | ⏳ Next |
| M2: Categories API | 2-3 hours | M1 | ⬜ |
| M3: Products API | 4-5 hours | M1, M2 | ⬜ |
| M4: Inventory API | 3-4 hours | M1, M3 | ⬜ |
| M5: Sales API | 4-5 hours | M1, M3, M4 | ⬜ |
| M6: Error Handling | 1-2 hours | Can be done in parallel | ⬜ |
| M7: Documentation | 1-2 hours | All above | ⬜ |

**Total Estimated:** 19-27 hours  
**Completed:** ~3 hours (M0)

---

## Pre-requisites

Before starting Phase 1:

- [x] Phase 0 completed
- [x] Docker Desktop installed
- [x] Local PostgreSQL running via Docker
- [x] Database schema executed locally
- [x] Multi-environment configuration (dev/stage/prod)

---

## Milestone 0: Local Development Environment

**Goal:** Set up local PostgreSQL database using Docker before connecting to Supabase Cloud.

### Why Local First?

- ✅ No internet dependency during development
- ✅ Faster database operations (no network latency)
- ✅ Free unlimited testing
- ✅ Easy reset/rebuild database
- ✅ Same PostgreSQL as Supabase (compatibility)

### Tasks

| # | Task | Description | Status |
|---|------|-------------|--------|
| 0.1 | Install Docker Desktop | Download and install Docker | ✅ |
| 0.2 | Create docker-compose.yml | PostgreSQL + pgAdmin config | ✅ |
| 0.3 | Start local database | `docker-compose up -d` | ✅ |
| 0.4 | Execute database schema | Run `schema.sql` in local DB | ✅ |
| 0.5 | Update database client | Support both local and Supabase | ✅ |
| 0.6 | Multi-environment config | `.env.development`, `.env.staging`, `.env.production` | ✅ |
| 0.7 | Test database connection | Verify health endpoint | ✅ |
| 0.8 | Hatch environments | Configure `hatch run dev/stage/prod:start` | ✅ |
| 0.9 | Reorganize db folder | Move `schema.sql` to `db/` folder | ✅ |
| 0.10 | Add seed data | Create `db/seeds/seed_data.sql` with test data | ✅ |

### Seed Data Summary

| Table | Records | Description |
|-------|---------|-------------|
| Categories | 10 | Bebidas, Lacteos, Abarrotes, etc. |
| Products | 35 | Bolivian products with prices in Bs |
| Sales | 2 | Sample transactions |
| Inventory Movements | 10 | Initial stock entries |

### Deliverables ✅

```
Backend-ComercialComarapa/
├── docker-compose.yml              # PostgreSQL + pgAdmin (auto-seeds)
├── db/
│   ├── schema.sql                  # Database schema
│   ├── seeds/
│   │   └── seed_data.sql           # Test data (35 products)
│   └── migrations/                 # Future migrations
├── .env.development                # Local Docker config
├── .env.staging                    # Supabase staging config
├── .env.production                 # Supabase production config
├── .env.example                    # Template reference
├── pyproject.toml                  # Hatch multi-environment config
└── src/comercial_comarapa/
    ├── config.py                   # Pydantic settings
    ├── main.py                     # FastAPI app + health endpoint
    └── db/
        ├── database.py             # Unified dual-mode DB client
        └── supabase.py             # Supabase client
```

### Commands Available

```bash
# Start server
hatch run dev:start     # Development (Docker PostgreSQL)
hatch run stage:start   # Staging (Supabase)
hatch run prod:start    # Production (Supabase)

# Tools
hatch run lint          # Check code
hatch run format        # Format code
hatch run test          # Run tests

# Docker
docker-compose up -d              # Start containers
docker-compose down -v            # Reset database with fresh seeds
```

### Endpoints Available

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check with DB status |
| GET | `/docs` | Swagger UI |

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: comercial_comarapa_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: comercial_comarapa
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: comercial_comarapa_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### Environment Configuration

```env
# .env.example (updated)

# =============================================================================
# DATABASE MODE: "local" or "supabase"
# =============================================================================
DATABASE_MODE=local

# -----------------------------------------------------------------------------
# Local PostgreSQL (when DATABASE_MODE=local)
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/comercial_comarapa

# -----------------------------------------------------------------------------
# Supabase (when DATABASE_MODE=supabase)
# -----------------------------------------------------------------------------
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-supabase-anon-key
```

### Database Client Architecture

```
                    ┌─────────────────┐
                    │   config.py     │
                    │ DATABASE_MODE   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  database.py    │
                    │  get_db_client()│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │  DATABASE_MODE  │          │  DATABASE_MODE  │
     │    = "local"    │          │   = "supabase"  │
     └────────┬────────┘          └────────┬────────┘
              │                             │
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │   asyncpg /     │          │    Supabase     │
     │   psycopg       │          │     Client      │
     └─────────────────┘          └─────────────────┘
```

### Commands Reference

```bash
# Start local database
docker-compose up -d

# View logs
docker-compose logs -f postgres

# Stop database
docker-compose down

# Reset database (delete all data)
docker-compose down -v
docker-compose up -d

# Access pgAdmin
# URL: http://localhost:5050
# Email: admin@local.com
# Password: admin

# Connect to PostgreSQL via CLI
docker exec -it comercial_comarapa_db psql -U postgres -d comercial_comarapa
```

### Success Criteria (M0)

| # | Criteria | Validation |
|---|----------|------------|
| 1 | Docker Desktop running | `docker --version` works |
| 2 | PostgreSQL container up | `docker ps` shows container |
| 3 | Schema executed | Tables visible in pgAdmin |
| 4 | App connects to local DB | `/health` shows `database: connected` |
| 5 | CRUD test works | Insert/select via pgAdmin |

---

## Milestone 1: Core Models (Pydantic Schemas)

**Goal:** Create all Pydantic models for request/response validation.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 1.1 | Create common models (pagination, responses) | `models/common.py` | ⬜ |
| 1.2 | Create Category schemas | `models/category.py` | ⬜ |
| 1.3 | Create Product schemas | `models/product.py` | ⬜ |
| 1.4 | Create Inventory Movement schemas | `models/inventory.py` | ⬜ |
| 1.5 | Create Sale schemas | `models/sale.py` | ⬜ |
| 1.6 | Export all models in `__init__.py` | `models/__init__.py` | ⬜ |

### Deliverables

```
src/comercial_comarapa/models/
├── __init__.py         # Export all models
├── common.py           # APIResponse, PaginatedResponse, ErrorResponse
├── category.py         # CategoryCreate, CategoryUpdate, CategoryResponse
├── product.py          # ProductCreate, ProductUpdate, ProductResponse, ProductFilter
├── inventory.py        # StockEntry, StockExit, MovementResponse, MovementType
└── sale.py             # SaleCreate, SaleItemCreate, SaleResponse, SaleStatus
```

### Model Specifications

#### 1.1 Common Models (`models/common.py`)

```python
# Pagination
class PaginationParams:
    page: int = 1
    page_size: int = 20

class PaginatedResponse[T]:
    success: bool
    data: list[T]
    pagination: PaginationMeta

class PaginationMeta:
    page: int
    page_size: int
    total_items: int
    total_pages: int

# Standard Responses
class APIResponse[T]:
    success: bool
    data: T | None
    message: str | None

class ErrorDetail:
    code: str
    message: str
    details: list[dict] | None

class ErrorResponse:
    success: bool = False
    error: ErrorDetail
```

#### 1.2 Category Models (`models/category.py`)

```python
class CategoryBase:
    name: str  # max 100 chars
    description: str | None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate:
    name: str | None
    description: str | None

class CategoryResponse(CategoryBase):
    id: UUID
    created_at: datetime
```

#### 1.3 Product Models (`models/product.py`)

```python
class ProductBase:
    sku: str  # max 50 chars, unique
    name: str  # max 255 chars
    description: str | None
    category_id: UUID | None
    unit_price: Decimal  # >= 0
    cost_price: Decimal | None  # >= 0
    min_stock_level: int = 5  # >= 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate:
    # All fields optional for partial updates
    sku: str | None
    name: str | None
    ...

class ProductResponse(ProductBase):
    id: UUID
    current_stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None  # Nested

class ProductFilter:
    category_id: UUID | None
    min_price: Decimal | None
    max_price: Decimal | None
    in_stock: bool | None
    is_active: bool = True
    search: str | None  # Search in name/sku
```

#### 1.4 Inventory Models (`models/inventory.py`)

```python
class MovementType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ADJUSTMENT = "ADJUSTMENT"

class MovementReason(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"
    CORRECTION = "CORRECTION"
    OTHER = "OTHER"

class StockEntryRequest:
    product_id: UUID
    quantity: int  # > 0
    reason: MovementReason = PURCHASE
    notes: str | None

class StockExitRequest:
    product_id: UUID
    quantity: int  # > 0
    reason: MovementReason
    notes: str | None

class StockAdjustmentRequest:
    product_id: UUID
    new_stock: int  # >= 0
    reason: MovementReason = CORRECTION
    notes: str | None

class MovementResponse:
    id: UUID
    product_id: UUID
    product_name: str  # Denormalized for convenience
    movement_type: MovementType
    quantity: int
    reason: MovementReason
    previous_stock: int
    new_stock: int
    notes: str | None
    created_at: datetime
```

#### 1.5 Sale Models (`models/sale.py`)

```python
class SaleStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class SaleItemCreate:
    product_id: UUID
    quantity: int  # > 0
    unit_price: Decimal | None  # If None, use product.unit_price
    discount: Decimal = 0

class SaleCreate:
    items: list[SaleItemCreate]  # min 1 item
    discount: Decimal = 0
    notes: str | None

class SaleItemResponse:
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal
    discount: Decimal
    subtotal: Decimal

class SaleResponse:
    id: UUID
    sale_number: str
    sale_date: datetime
    items: list[SaleItemResponse]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    status: SaleStatus
    notes: str | None
    created_at: datetime

class DailySummary:
    date: date
    total_transactions: int
    gross_sales: Decimal
    total_discounts: Decimal
    net_sales: Decimal
```

---

## Milestone 2: Categories API

**Goal:** Implement CRUD endpoints for product categories.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 2.1 | Create Category repository | `db/repositories/category_repo.py` | ⬜ |
| 2.2 | Create Category service | `services/category_service.py` | ⬜ |
| 2.3 | Create Categories router | `api/v1/categories.py` | ⬜ |
| 2.4 | Register router in main app | `api/v1/router.py` | ⬜ |
| 2.5 | Test endpoints manually | Swagger UI | ⬜ |

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/categories` | List all categories | - | `list[CategoryResponse]` |
| GET | `/api/v1/categories/{id}` | Get by ID | - | `CategoryResponse` |
| POST | `/api/v1/categories` | Create category | `CategoryCreate` | `CategoryResponse` (201) |
| PUT | `/api/v1/categories/{id}` | Update category | `CategoryUpdate` | `CategoryResponse` |
| DELETE | `/api/v1/categories/{id}` | Delete category | - | 204 No Content |

### Business Rules

- Category name must be unique
- Cannot delete category with assigned products (return 409 Conflict)

---

## Milestone 3: Products API

**Goal:** Implement CRUD + search + filtering for products.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 3.1 | Create Product repository | `db/repositories/product_repo.py` | ⬜ |
| 3.2 | Create Product service | `services/product_service.py` | ⬜ |
| 3.3 | Create Products router | `api/v1/products.py` | ⬜ |
| 3.4 | Implement search functionality | `services/product_service.py` | ⬜ |
| 3.5 | Implement low-stock endpoint | `api/v1/products.py` | ⬜ |
| 3.6 | Register router | `api/v1/router.py` | ⬜ |
| 3.7 | Test endpoints | Swagger UI | ⬜ |

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/products` | List products (paginated) | `ProductFilter` + pagination | `PaginatedResponse[ProductResponse]` |
| GET | `/api/v1/products/{id}` | Get by ID | - | `ProductResponse` |
| GET | `/api/v1/products/sku/{sku}` | Get by SKU | - | `ProductResponse` |
| POST | `/api/v1/products` | Create product | `ProductCreate` | `ProductResponse` (201) |
| PUT | `/api/v1/products/{id}` | Update product | `ProductUpdate` | `ProductResponse` |
| DELETE | `/api/v1/products/{id}` | Soft delete | - | 204 No Content |
| GET | `/api/v1/products/search` | Search products | `?q=term` | `list[ProductResponse]` |
| GET | `/api/v1/products/low-stock` | Low stock alerts | - | `list[ProductResponse]` |

### Business Rules

- SKU must be unique
- Soft delete (set `is_active = false`)
- Low stock = `current_stock <= min_stock_level`
- Search in `name` and `sku` fields (case-insensitive)

---

## Milestone 4: Inventory API

**Goal:** Implement stock movements and history.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 4.1 | Create Inventory repository | `db/repositories/inventory_repo.py` | ⬜ |
| 4.2 | Create Inventory service | `services/inventory_service.py` | ⬜ |
| 4.3 | Implement stock entry logic | `services/inventory_service.py` | ⬜ |
| 4.4 | Implement stock exit logic | `services/inventory_service.py` | ⬜ |
| 4.5 | Implement stock adjustment | `services/inventory_service.py` | ⬜ |
| 4.6 | Create Inventory router | `api/v1/inventory.py` | ⬜ |
| 4.7 | Register router | `api/v1/router.py` | ⬜ |
| 4.8 | Test endpoints | Swagger UI | ⬜ |

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/inventory/movements` | List all movements | filters + pagination | `PaginatedResponse[MovementResponse]` |
| GET | `/api/v1/inventory/movements/{product_id}` | Movements by product | - | `list[MovementResponse]` |
| POST | `/api/v1/inventory/entry` | Register stock entry | `StockEntryRequest` | `MovementResponse` (201) |
| POST | `/api/v1/inventory/exit` | Register stock exit | `StockExitRequest` | `MovementResponse` (201) |
| POST | `/api/v1/inventory/adjustment` | Stock adjustment | `StockAdjustmentRequest` | `MovementResponse` (201) |

### Business Rules

- Entry: `new_stock = current_stock + quantity`
- Exit: `new_stock = current_stock - quantity` (fail if insufficient)
- Adjustment: `new_stock = specified value`
- Always record `previous_stock` and `new_stock`
- Update `products.current_stock` atomically

---

## Milestone 5: Sales API

**Goal:** Implement sales registration with automatic inventory updates.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 5.1 | Create Sale repository | `db/repositories/sale_repo.py` | ⬜ |
| 5.2 | Create Sale service | `services/sale_service.py` | ⬜ |
| 5.3 | Implement create sale with items | `services/sale_service.py` | ⬜ |
| 5.4 | Implement inventory deduction | `services/sale_service.py` | ⬜ |
| 5.5 | Implement cancel sale (restore stock) | `services/sale_service.py` | ⬜ |
| 5.6 | Implement daily summary | `services/sale_service.py` | ⬜ |
| 5.7 | Create Sales router | `api/v1/sales.py` | ⬜ |
| 5.8 | Register router | `api/v1/router.py` | ⬜ |
| 5.9 | Test endpoints | Swagger UI | ⬜ |

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/sales` | List sales | date filters + pagination | `PaginatedResponse[SaleResponse]` |
| GET | `/api/v1/sales/{id}` | Get sale with items | - | `SaleResponse` |
| POST | `/api/v1/sales` | Create new sale | `SaleCreate` | `SaleResponse` (201) |
| POST | `/api/v1/sales/{id}/cancel` | Cancel sale | `{reason: str}` | `SaleResponse` |
| GET | `/api/v1/sales/summary/daily` | Daily summary | `?date=YYYY-MM-DD` | `DailySummary` |

### Business Rules

- Sale number auto-generated: `YYYY-NNNNNN`
- Each item deducts from product stock
- Validate sufficient stock before creating sale
- Cancel: restore stock, set status = CANCELLED
- Cannot cancel already cancelled sale

### Sale Creation Flow

```
1. Validate all products exist and are active
2. Validate sufficient stock for each item
3. Calculate line subtotals
4. Calculate sale totals (subtotal, discount, tax, total)
5. Create sale record
6. Create sale_items records
7. For each item:
   - Create inventory_movement (EXIT, reason=SALE)
   - Update product.current_stock
8. Return complete sale with items
```

---

## Milestone 6: Error Handling

**Goal:** Implement consistent error responses.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 6.1 | Create custom exceptions | `core/exceptions.py` | ⬜ |
| 6.2 | Create exception handlers | `core/exceptions.py` | ⬜ |
| 6.3 | Register handlers in main.py | `main.py` | ⬜ |
| 6.4 | Create response helpers | `core/responses.py` | ⬜ |

### Exception Hierarchy

```python
# core/exceptions.py

class APIException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

class NotFoundError(APIException):
    status_code = 404

class ProductNotFoundError(NotFoundError):
    error_code = "PRODUCT_NOT_FOUND"

class CategoryNotFoundError(NotFoundError):
    error_code = "CATEGORY_NOT_FOUND"

class SaleNotFoundError(NotFoundError):
    error_code = "SALE_NOT_FOUND"

class ValidationError(APIException):
    status_code = 400

class DuplicateSKUError(ValidationError):
    error_code = "DUPLICATE_SKU"

class InsufficientStockError(ValidationError):
    status_code = 422
    error_code = "INSUFFICIENT_STOCK"

class ConflictError(APIException):
    status_code = 409

class CategoryHasProductsError(ConflictError):
    error_code = "CATEGORY_HAS_PRODUCTS"

class SaleAlreadyCancelledError(ConflictError):
    error_code = "SALE_ALREADY_CANCELLED"
```

---

## Milestone 7: Final Documentation

**Goal:** Complete README and API documentation.

### Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 7.1 | Update README with API endpoints | `README.md` | ⬜ |
| 7.2 | Add API examples | `Documentation/api/examples.md` | ⬜ |
| 7.3 | Update PRD status | `Documentation/project-init/PRD.md` | ⬜ |
| 7.4 | Final Swagger review | `/docs` | ⬜ |

---

## Implementation Order

### Recommended Sequence

```
Day 1: M0 (Local Environment Setup)
       ├── Install Docker Desktop
       ├── Create docker-compose.yml
       ├── Start PostgreSQL + pgAdmin
       └── Verify schema and connection

Day 2: M1 (Core Models) + M6 (Error Handling)
       ├── Create all Pydantic models
       └── Implement exception classes

Day 3: M2 (Categories API)
       ├── Repository + Service + Router
       └── Test CRUD via Swagger

Day 4: M3 (Products API) - Part 1
       ├── Basic CRUD endpoints
       └── Repository + Service

Day 5: M3 (Products API) - Part 2
       ├── Search functionality
       ├── Filtering
       └── Low-stock endpoint

Day 6: M4 (Inventory API)
       ├── Stock entry/exit/adjustment
       └── Movement history

Day 7: M5 (Sales API)
       ├── Create sale with items
       ├── Inventory deduction
       └── Cancel sale (restore stock)

Day 8: M7 (Documentation) + Testing
       ├── Update README
       ├── End-to-end testing
       └── Final commit
```

### Dependency Graph

```
M0: Local Environment ◄─── START HERE
    │
    ▼
M1: Core Models
    │
    ├──► M2: Categories API
    │         │
    │         ▼
    ├──► M3: Products API ◄────┐
    │         │                │
    │         ▼                │
    ├──► M4: Inventory API ────┤
    │         │                │
    │         ▼                │
    └──► M5: Sales API ◄───────┘
              │
              ▼
         M7: Documentation

M6: Error Handling (parallel with M1)
```

---

## Testing Checklist

### Per Milestone

- [ ] All endpoints return correct status codes
- [ ] Validation errors return 400/422
- [ ] Not found returns 404
- [ ] Swagger documentation accurate
- [ ] Ruff linting passes

### End-to-End Flow Test

```
1. Create category "Beverages"
2. Create product "Coca Cola 2L" in Beverages
3. Add stock entry: +100 units
4. Verify product.current_stock = 100
5. Create sale: 5 units of Coca Cola
6. Verify product.current_stock = 95
7. Verify inventory_movement created
8. Cancel sale
9. Verify product.current_stock = 100 (restored)
10. Get low-stock products (should be empty)
11. Create stock exit: 96 units
12. Get low-stock products (should include Coca Cola)
```

---

## File Creation Summary

### New Files to Create

```
BackEnd-CC/
├── docker-compose.yml      # M0 - PostgreSQL + pgAdmin
│
└── src/comercial_comarapa/
    │
    ├── db/
    │   ├── database.py         # M0 - Unified DB client
    │   ├── supabase.py         # M0 - Updated for dual mode
    │   └── repositories/
    │       ├── base.py             # M2
    │       ├── category_repo.py    # M2
    │       ├── product_repo.py     # M3
    │       ├── inventory_repo.py   # M4
    │       └── sale_repo.py        # M5
    │
    ├── models/
    │   ├── common.py           # M1
    │   ├── category.py         # M1
    │   ├── product.py          # M1
    │   ├── inventory.py        # M1
    │   └── sale.py             # M1
    │
    ├── services/
    │   ├── category_service.py   # M2
    │   ├── product_service.py    # M3
    │   ├── inventory_service.py  # M4
    │   └── sale_service.py       # M5
    │
    ├── api/
    │   ├── deps.py             # M2
    │   └── v1/
    │       ├── router.py       # M2
    │       ├── categories.py   # M2
    │       ├── products.py     # M3
    │       ├── inventory.py    # M4
    │       └── sales.py        # M5
    │
    └── core/
        ├── exceptions.py       # M6
        └── responses.py        # M6
```

**Total new files:** 22

---

## Success Criteria Reminder

Phase 1 is complete when:

- [x] All CRUD operations work via Swagger
- [x] Products can be searched and filtered
- [x] Low stock alerts work correctly
- [x] Sales deduct inventory automatically
- [x] Sale cancellation restores stock
- [x] All endpoints return proper error responses
- [x] Ruff linting passes
- [x] README updated with API info

