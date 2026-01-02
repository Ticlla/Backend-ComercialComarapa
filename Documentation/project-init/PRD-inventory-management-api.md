# Product Requirements Document (PRD)
## Inventory Management REST API - Comercial Comarapa

**Document Version:** 1.0  
**Created:** January 2, 2026  
**Status:** Draft  

---

## 1. Executive Summary

This document outlines the requirements for building a REST API backend system for **Comercial Comarapa**, a retail store managing approximately 1,000 products. The system will handle product management, inventory control, and sales registration using modern Python technologies.

> **🎯 Current Phase: 1 - Backend REST API**
> 
> | Phase | Focus | Status |
> |-------|-------|--------|
> | **Phase 0** | Project setup, Hatch config, dependencies, Supabase connection | ✅ Completed |
> | **Phase 1** | Backend REST API (CRUD, inventory, sales) | 🔄 In Progress |
> | **Phase 2** | Frontend application | ⬜ Future |

### Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Language | Python 3.14 | Latest version, industry standard, excellent ecosystem |
| Project Manager | Hatch | Modern dependency management, testing, builds |
| Web Framework | **FastAPI** | Async support, automatic OpenAPI docs, Pydantic integration, high performance |
| Database | Supabase (PostgreSQL) | Managed PostgreSQL, real-time capabilities, built-in auth |
| Validation | Pydantic v2 | Native FastAPI integration, type safety |
| Linting | Ruff | Fast, comprehensive Python linter |

> **Framework Choice: FastAPI** was selected over Flask for:
> - Native async/await support
> - Automatic Swagger/OpenAPI documentation
> - Built-in request validation with Pydantic
> - Better performance for I/O-bound operations
> - Type hints enforcement

---

## 2. Project Scope

> **Current Focus: Phase 0 - Project Configuration**
> 
> Before implementing the API, we must establish a solid project foundation:
> Hatch setup, dependencies, folder structure, and database connection.
> 
> **Phase 1** will focus on Backend REST API development.
> **Phase 2** will address Frontend development.

### 2.1 In Scope (Phase 0 - Configuration)

- [x] Initialize project with Hatch
- [x] Configure `pyproject.toml` with metadata and dependencies
- [x] Set up project folder structure (`src/comercial_comarapa/`)
- [x] Configure Ruff linting rules
- [x] Create environment configuration (`.env.example`, `config.py`)
- [x] Define Hatch scripts (`dev`, `lint`, `format`, `test`)
- [x] Create FastAPI skeleton with health endpoint
- [x] Implement Supabase client connection

### 2.2 In Scope (Phase 1 - Backend)

- [ ] Product CRUD operations
- [ ] Category CRUD operations
- [ ] Inventory movement tracking (entries/exits)
- [ ] Low stock alerts system
- [ ] Sales registration with line items
- [ ] Product search and filtering
- [ ] API documentation (Swagger/OpenAPI at `/docs`)
- [ ] Error handling and HTTP standard responses
- [ ] Input validation with Pydantic

### 2.3 Out of Scope (Phase 0 & 1)

- [ ] Frontend/UI application (Phase 2)
- [ ] Payment gateway integration
- [ ] Multi-store support
- [ ] Reporting and analytics dashboard
- [ ] Mobile application
- [ ] Real-time notifications (WebSockets)

### 2.4 Optional Features (Phase 1)

- [ ] JWT Authentication
- [ ] Operation logging/audit trail
- [ ] Unit tests with pytest (70% coverage)

---

## 3. Functional Requirements

### 3.1 Product Management (FR-001)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001.1 | Create new products with name, SKU, description, price, category | High |
| FR-001.2 | Retrieve single product by ID or SKU | High |
| FR-001.3 | List all products with pagination | High |
| FR-001.4 | Update product information | High |
| FR-001.5 | Soft delete products (mark as inactive) | High |
| FR-001.6 | Search products by name, SKU, or category | High |
| FR-001.7 | Filter products by category, price range, stock status | Medium |

#### Product Entity Schema

```
Product {
    id: UUID (PK)
    sku: String (unique, indexed)
    name: String (indexed)
    description: Text (nullable)
    category_id: UUID (FK -> Category)
    unit_price: Decimal(10,2)
    cost_price: Decimal(10,2)
    current_stock: Integer (default: 0)
    min_stock_level: Integer (default: 5)
    is_active: Boolean (default: true)
    created_at: Timestamp
    updated_at: Timestamp
}
```

### 3.2 Category Management (FR-002)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-002.1 | Create product categories | Medium |
| FR-002.2 | List all categories | Medium |
| FR-002.3 | Update category information | Medium |
| FR-002.4 | Delete category (only if no products assigned) | Low |

#### Category Entity Schema

```
Category {
    id: UUID (PK)
    name: String (unique)
    description: Text (nullable)
    created_at: Timestamp
}
```

### 3.3 Inventory Management (FR-003)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-003.1 | Register stock entry (purchase/restock) | High |
| FR-003.2 | Register stock exit (sale/adjustment/loss) | High |
| FR-003.3 | View inventory movement history by product | High |
| FR-003.4 | Get low stock alerts (products below min_stock_level) | High |
| FR-003.5 | Bulk stock update capability | Medium |
| FR-003.6 | Stock adjustment with reason codes | Medium |

#### Inventory Movement Entity Schema

```
InventoryMovement {
    id: UUID (PK)
    product_id: UUID (FK -> Product)
    movement_type: Enum ['ENTRY', 'EXIT', 'ADJUSTMENT']
    quantity: Integer
    reason: Enum ['PURCHASE', 'SALE', 'RETURN', 'DAMAGE', 'CORRECTION', 'OTHER']
    reference_id: UUID (nullable, FK -> Sale if applicable)
    notes: Text (nullable)
    previous_stock: Integer
    new_stock: Integer
    created_at: Timestamp
    created_by: UUID (nullable, FK -> User)
}
```

### 3.4 Sales Management (FR-004)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-004.1 | Create new sale with multiple line items | High |
| FR-004.2 | Retrieve sale by ID with all details | High |
| FR-004.3 | List sales with date range filtering | High |
| FR-004.4 | Cancel/void a sale (restore stock) | Medium |
| FR-004.5 | Daily sales summary | Medium |

#### Sale Entity Schema

```
Sale {
    id: UUID (PK)
    sale_number: String (unique, auto-generated)
    sale_date: Timestamp
    subtotal: Decimal(10,2)
    discount: Decimal(10,2) (default: 0)
    tax: Decimal(10,2) (default: 0)
    total: Decimal(10,2)
    status: Enum ['COMPLETED', 'CANCELLED']
    notes: Text (nullable)
    created_at: Timestamp
    created_by: UUID (nullable, FK -> User)
}

SaleItem {
    id: UUID (PK)
    sale_id: UUID (FK -> Sale)
    product_id: UUID (FK -> Product)
    quantity: Integer
    unit_price: Decimal(10,2)
    discount: Decimal(10,2) (default: 0)
    subtotal: Decimal(10,2)
}
```

---

## 4. API Endpoints Specification

### 4.1 Products API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/products` | List products (paginated, filterable) |
| `GET` | `/api/v1/products/{id}` | Get product by ID |
| `GET` | `/api/v1/products/sku/{sku}` | Get product by SKU |
| `POST` | `/api/v1/products` | Create new product |
| `PUT` | `/api/v1/products/{id}` | Update product |
| `DELETE` | `/api/v1/products/{id}` | Soft delete product |
| `GET` | `/api/v1/products/search` | Search products |
| `GET` | `/api/v1/products/low-stock` | Get low stock products |

### 4.2 Categories API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/categories` | List all categories |
| `GET` | `/api/v1/categories/{id}` | Get category by ID |
| `POST` | `/api/v1/categories` | Create category |
| `PUT` | `/api/v1/categories/{id}` | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Delete category |

### 4.3 Inventory API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/inventory/movements` | List all movements (filterable) |
| `GET` | `/api/v1/inventory/movements/{product_id}` | Get movements by product |
| `POST` | `/api/v1/inventory/entry` | Register stock entry |
| `POST` | `/api/v1/inventory/exit` | Register stock exit |
| `POST` | `/api/v1/inventory/adjustment` | Stock adjustment |

### 4.4 Sales API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sales` | List sales (paginated, date filterable) |
| `GET` | `/api/v1/sales/{id}` | Get sale with items |
| `POST` | `/api/v1/sales` | Create new sale |
| `POST` | `/api/v1/sales/{id}/cancel` | Cancel sale |
| `GET` | `/api/v1/sales/summary/daily` | Daily sales summary |

### 4.5 Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/info` | API version info |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement | Target |
|-------------|--------|
| API Response Time | < 200ms (p95) for simple queries |
| Concurrent Users | Support 10+ simultaneous users |
| Database Queries | Optimized with proper indexing |

### 5.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Environment Variables | All secrets via `.env` file |
| Input Validation | Pydantic models for all requests |
| SQL Injection | Prevented via parameterized queries |
| CORS | Configurable allowed origins |

### 5.3 Code Quality

| Requirement | Tool/Standard |
|-------------|---------------|
| Linting | Ruff (run before commits) |
| Type Hints | Required for all functions |
| Documentation | Docstrings for public APIs |
| Testing | pytest with minimum 70% coverage (optional phase 1) |

---

## 6. Project Structure

```
BackEnd-CC/
├── pyproject.toml              # Hatch project configuration
├── README.md                   # Project documentation
├── .env.example                # Environment variables template
├── .gitignore
│
├── src/
│   └── comercial_comarapa/     # Main package
│       ├── __init__.py
│       ├── main.py             # FastAPI application entry point
│       ├── config.py           # Settings and configuration
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py         # Dependency injection
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py   # Main API router
│       │       ├── products.py
│       │       ├── categories.py
│       │       ├── inventory.py
│       │       └── sales.py
│       │
│       ├── models/             # Pydantic models (schemas)
│       │   ├── __init__.py
│       │   ├── product.py
│       │   ├── category.py
│       │   ├── inventory.py
│       │   ├── sale.py
│       │   └── common.py       # Shared models (pagination, responses)
│       │
│       ├── services/           # Business logic
│       │   ├── __init__.py
│       │   ├── product_service.py
│       │   ├── category_service.py
│       │   ├── inventory_service.py
│       │   └── sale_service.py
│       │
│       ├── db/                 # Database layer
│       │   ├── __init__.py
│       │   ├── supabase.py     # Supabase client
│       │   └── repositories/   # Data access layer
│       │       ├── __init__.py
│       │       ├── product_repo.py
│       │       ├── category_repo.py
│       │       ├── inventory_repo.py
│       │       └── sale_repo.py
│       │
│       └── core/               # Core utilities
│           ├── __init__.py
│           ├── exceptions.py   # Custom exceptions
│           ├── responses.py    # Standard API responses
│           └── logging.py      # Logging configuration (optional)
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_products.py
│   ├── test_inventory.py
│   └── test_sales.py
│
└── Documentation/
    ├── project-init/
    │   └── PRD-inventory-management-api.md
    ├── database/
    │   └── schema.sql          # Database schema for Supabase
    └── api/
        └── examples.md         # API usage examples
```

---

## 7. Database Schema (Supabase/PostgreSQL)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Categories table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    unit_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),
    current_stock INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for product search
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);

-- Inventory movements table
CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('ENTRY', 'EXIT', 'ADJUSTMENT')),
    quantity INTEGER NOT NULL,
    reason VARCHAR(20) NOT NULL CHECK (reason IN ('PURCHASE', 'SALE', 'RETURN', 'DAMAGE', 'CORRECTION', 'OTHER')),
    reference_id UUID,
    notes TEXT,
    previous_stock INTEGER NOT NULL,
    new_stock INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX idx_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_movements_date ON inventory_movements(created_at);

-- Sales table
CREATE TABLE sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_number VARCHAR(20) NOT NULL UNIQUE,
    sale_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subtotal DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    tax DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'COMPLETED' CHECK (status IN ('COMPLETED', 'CANCELLED')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_number ON sales(sale_number);

-- Sale items table
CREATE TABLE sale_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) NOT NULL
);

CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);

-- Function to update product timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products updated_at
CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

---

## 8. Environment Configuration

### Required Environment Variables

```env
# .env.example

# Application
APP_NAME=comercial-comarapa-api
APP_ENV=development
DEBUG=true
API_VERSION=v1

# Server
HOST=0.0.0.0
PORT=8000

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: JWT Authentication
# JWT_SECRET=your-super-secret-key
# JWT_ALGORITHM=HS256
# JWT_EXPIRE_MINUTES=60
```

---

## 9. Dependencies

### Core Dependencies

```toml
# pyproject.toml [project.dependencies]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "supabase>=2.3.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
]
```

### Development Dependencies

```toml
# pyproject.toml [tool.hatch.envs.default.dependencies]
dev-dependencies = [
    "ruff>=0.1.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",  # For TestClient
]
```

---

## 10. Milestones & Deliverables

### Phase 0: Project Configuration (Current)

| # | Task | Deliverables | Status |
|---|------|--------------|--------|
| 0.1 | **Hatch Initialization** | `pyproject.toml` with project metadata | ✅ Done |
| 0.2 | **Dependencies Setup** | Core & dev dependencies configured | ✅ Done |
| 0.3 | **Project Structure** | `src/comercial_comarapa/` folder hierarchy | ✅ Done |
| 0.4 | **Ruff Configuration** | Linting rules in `pyproject.toml` | ✅ Done |
| 0.5 | **Environment Config** | `.env.example`, `config.py` with pydantic-settings | ✅ Done |
| 0.6 | **Hatch Scripts** | `dev`, `lint`, `format`, `test` commands | ✅ Done |
| 0.7 | **FastAPI Skeleton** | Basic `main.py` with health endpoint | ✅ Done |
| 0.8 | **Supabase Client** | Database connection module | ✅ Done |

> **Note:** `.gitignore` already exists in the project.

**Phase 0 Deliverables:**
```
BackEnd-CC/
├── pyproject.toml          # Hatch configuration
├── README.md               # Setup instructions
├── .env.example            # Environment template
└── src/
    └── comercial_comarapa/
        ├── __init__.py
        ├── main.py         # FastAPI app (health endpoint)
        ├── config.py       # Settings class
        └── db/
            └── supabase.py # Supabase client
```

---

### Phase 1: Backend REST API

| # | Milestone | Deliverables | Priority | Status |
|---|-----------|--------------|----------|--------|
| M1 | **Core Models** | Pydantic schemas for all entities | High | ⬜ Pending |
| M2 | **Categories API** | CRUD endpoints | High | ⬜ Pending |
| M3 | **Products API** | CRUD + search + filtering + low-stock | High | ⬜ Pending |
| M4 | **Inventory API** | Stock entry/exit/adjustment, movement history | High | ⬜ Pending |
| M5 | **Sales API** | Create sale, list, cancel, daily summary | High | ⬜ Pending |
| M6 | **Error Handling** | Custom exceptions, standard responses | High | ⬜ Pending |
| M7 | **Final Documentation** | Complete README, API examples | High | ⬜ Pending |

### Phase 1: Optional Enhancements

| Feature | Priority | Status |
|---------|----------|--------|
| JWT Authentication | Medium | ⬜ Pending |
| Audit logging | Medium | ⬜ Pending |
| Unit tests (pytest, 70%+ coverage) | Medium | ⬜ Pending |

---

### Phase 2: Frontend (Future)

| Feature | Description |
|---------|-------------|
| Web Application | React/Vue frontend for store staff |
| Dashboard | Sales and inventory analytics |
| Mobile App | Optional mobile interface |

---

## 11. Success Criteria

### Phase 0 Success Criteria (Configuration)

| # | Criteria | Validation |
|---|----------|------------|
| 1 | Hatch project initializes correctly | `hatch env create` succeeds |
| 2 | All dependencies install | `hatch shell` activates environment |
| 3 | Ruff linting configured | `hatch run lint` runs without config errors |
| 4 | FastAPI server starts | `hatch run dev` launches on port 8000 |
| 5 | Health endpoint responds | `GET /health` returns 200 OK |
| 6 | Supabase client connects | Connection test passes |
| 7 | Environment loading works | `.env` variables accessible via `config.py` |
| 8 | Project structure complete | All folders/files in place |

### Phase 1 Success Criteria (Backend)

| # | Criteria | Validation |
|---|----------|------------|
| 1 | All CRUD operations functional | Manual API testing via Swagger |
| 2 | API responds within 200ms (p95) | Response time monitoring |
| 3 | Swagger docs accessible at `/docs` | Browser verification |
| 4 | Ruff linting passes with no errors | `hatch run lint` exits 0 |
| 5 | Clear setup instructions in README | New dev can run in < 10 min |
| 6 | Proper HTTP status codes | 200, 201, 400, 404, 422, 500 |
| 7 | Supabase integration working | Data persists correctly |
| 8 | Low stock alerts functional | Products below threshold returned |
| 9 | Sales affect inventory | Stock decreases on sale creation |

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Supabase rate limits | Medium | Implement caching, batch operations |
| Data consistency in sales | High | Use database transactions |
| Stock synchronization | High | Atomic operations, optimistic locking |

---

## Appendix A: API Response Standards

### Success Response

```json
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully"
}
```

### Error Response

```json
{
    "success": false,
    "error": {
        "code": "PRODUCT_NOT_FOUND",
        "message": "Product with ID xyz not found"
    }
}
```

### Paginated Response

```json
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_items": 150,
        "total_pages": 8
    }
}
```

---

## Appendix B: HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT |
| 201 | Successful POST (created) |
| 204 | Successful DELETE |
| 400 | Bad request / Validation error |
| 404 | Resource not found |
| 409 | Conflict (duplicate SKU, etc.) |
| 422 | Unprocessable entity |
| 500 | Internal server error |

---

**Document Approval**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| Developer | | | |

