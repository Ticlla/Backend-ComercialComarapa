# API Usage Examples

This document provides practical examples for using the Comercial Comarapa REST API.

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://your-domain.com/api/v1
```

---

## Authentication (Optional)

If JWT authentication is enabled:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'

# Use token in subsequent requests
curl http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer <your-token>"
```

---

## Products API

### Create a Product

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "BEV-001",
    "name": "Coca Cola 2L",
    "description": "Coca Cola soft drink, 2 liter bottle",
    "category_id": "uuid-of-beverages-category",
    "unit_price": 15.50,
    "cost_price": 12.00,
    "min_stock_level": 10
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sku": "BEV-001",
    "name": "Coca Cola 2L",
    "description": "Coca Cola soft drink, 2 liter bottle",
    "category_id": "uuid-of-beverages-category",
    "unit_price": 15.50,
    "cost_price": 12.00,
    "current_stock": 0,
    "min_stock_level": 10,
    "is_active": true,
    "created_at": "2026-01-02T10:30:00Z",
    "updated_at": "2026-01-02T10:30:00Z"
  },
  "message": "Product created successfully"
}
```

### List Products (with pagination)

```bash
# Basic listing
curl http://localhost:8000/api/v1/products

# With pagination
curl "http://localhost:8000/api/v1/products?page=1&page_size=20"

# With filtering
curl "http://localhost:8000/api/v1/products?category_id=uuid&is_active=true"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sku": "BEV-001",
      "name": "Coca Cola 2L",
      "current_stock": 50,
      "unit_price": 15.50
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 156,
    "total_pages": 8
  }
}
```

### Search Products

```bash
# Search by name
curl "http://localhost:8000/api/v1/products/search?q=coca"

# Search with category filter
curl "http://localhost:8000/api/v1/products/search?q=cola&category_id=uuid"
```

### Get Product by SKU

```bash
curl http://localhost:8000/api/v1/products/sku/BEV-001
```

### Update Product

```bash
curl -X PUT http://localhost:8000/api/v1/products/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "unit_price": 16.00,
    "min_stock_level": 15
  }'
```

### Get Low Stock Products

```bash
curl http://localhost:8000/api/v1/products/low-stock
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "sku": "SNK-005",
      "name": "Oreo Cookies",
      "current_stock": 3,
      "min_stock_level": 10,
      "units_needed": 7
    }
  ]
}
```

---

## Categories API

### Create Category

```bash
curl -X POST http://localhost:8000/api/v1/categories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beverages",
    "description": "Drinks and refreshments"
  }'
```

### List All Categories

```bash
curl http://localhost:8000/api/v1/categories
```

---

## Inventory API

### Register Stock Entry (Purchase/Restock)

```bash
curl -X POST http://localhost:8000/api/v1/inventory/entry \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 100,
    "reason": "PURCHASE",
    "notes": "Weekly restock from distributor"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "movement-uuid",
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "movement_type": "ENTRY",
    "quantity": 100,
    "reason": "PURCHASE",
    "previous_stock": 0,
    "new_stock": 100,
    "created_at": "2026-01-02T11:00:00Z"
  },
  "message": "Stock entry registered successfully"
}
```

### Register Stock Exit (Manual adjustment)

```bash
curl -X POST http://localhost:8000/api/v1/inventory/exit \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 5,
    "reason": "DAMAGE",
    "notes": "Damaged during storage"
  }'
```

### Stock Adjustment (Correction)

```bash
curl -X POST http://localhost:8000/api/v1/inventory/adjustment \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "new_stock": 95,
    "reason": "CORRECTION",
    "notes": "Physical count adjustment"
  }'
```

### View Movement History

```bash
# All movements for a product
curl "http://localhost:8000/api/v1/inventory/movements/550e8400-e29b-41d4-a716-446655440000"

# Filter by date range
curl "http://localhost:8000/api/v1/inventory/movements?start_date=2026-01-01&end_date=2026-01-31"
```

---

## Sales API

### Create a Sale

```bash
curl -X POST http://localhost:8000/api/v1/sales \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "quantity": 2,
        "unit_price": 15.50,
        "discount": 0
      },
      {
        "product_id": "another-product-uuid",
        "quantity": 1,
        "unit_price": 8.00,
        "discount": 0.50
      }
    ],
    "discount": 0,
    "notes": "Cash payment"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "sale-uuid",
    "sale_number": "2026-000001",
    "sale_date": "2026-01-02T12:30:00Z",
    "items": [
      {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "product_name": "Coca Cola 2L",
        "quantity": 2,
        "unit_price": 15.50,
        "subtotal": 31.00
      },
      {
        "product_id": "another-product-uuid",
        "product_name": "Chips",
        "quantity": 1,
        "unit_price": 8.00,
        "discount": 0.50,
        "subtotal": 7.50
      }
    ],
    "subtotal": 38.50,
    "discount": 0,
    "tax": 0,
    "total": 38.50,
    "status": "COMPLETED"
  },
  "message": "Sale completed successfully"
}
```

### Get Sale Details

```bash
curl http://localhost:8000/api/v1/sales/sale-uuid
```

### List Sales (with date filter)

```bash
# Today's sales
curl "http://localhost:8000/api/v1/sales?date=2026-01-02"

# Date range
curl "http://localhost:8000/api/v1/sales?start_date=2026-01-01&end_date=2026-01-31"
```

### Cancel a Sale

```bash
curl -X POST http://localhost:8000/api/v1/sales/sale-uuid/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Customer returned items"
  }'
```

### Daily Sales Summary

```bash
curl "http://localhost:8000/api/v1/sales/summary/daily?date=2026-01-02"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2026-01-02",
    "total_transactions": 45,
    "gross_sales": 5680.50,
    "total_discounts": 125.00,
    "net_sales": 5555.50,
    "top_products": [
      {
        "product_id": "uuid",
        "name": "Coca Cola 2L",
        "quantity_sold": 28
      }
    ]
  }
}
```

---

## Error Responses

### Validation Error (400)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "unit_price",
        "message": "must be greater than 0"
      }
    ]
  }
}
```

### Not Found (404)

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID xyz not found"
  }
}
```

### Conflict (409)

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_SKU",
    "message": "A product with SKU 'BEV-001' already exists"
  }
}
```

### Insufficient Stock (422)

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Not enough stock for product 'Coca Cola 2L'. Available: 5, Requested: 10"
  }
}
```

---

## Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "timestamp": "2026-01-02T12:00:00Z"
}
```

---

## Using with HTTPie

For more readable command-line testing, you can use [HTTPie](https://httpie.io/):

```bash
# Create product
http POST localhost:8000/api/v1/products \
  sku=BEV-001 \
  name="Coca Cola 2L" \
  unit_price:=15.50

# List products
http localhost:8000/api/v1/products page==1 page_size==10

# Search
http localhost:8000/api/v1/products/search q==coca
```

---

## Python Client Example

```python
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Create a product
        response = await client.post(
            f"{BASE_URL}/products",
            json={
                "sku": "BEV-001",
                "name": "Coca Cola 2L",
                "unit_price": 15.50,
                "min_stock_level": 10
            }
        )
        product = response.json()["data"]
        
        # Add stock
        await client.post(
            f"{BASE_URL}/inventory/entry",
            json={
                "product_id": product["id"],
                "quantity": 100,
                "reason": "PURCHASE"
            }
        )
        
        # Create a sale
        await client.post(
            f"{BASE_URL}/sales",
            json={
                "items": [
                    {
                        "product_id": product["id"],
                        "quantity": 2,
                        "unit_price": 15.50
                    }
                ]
            }
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

