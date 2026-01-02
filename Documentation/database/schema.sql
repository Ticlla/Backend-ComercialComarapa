-- ============================================
-- Comercial Comarapa - Database Schema
-- Database: Supabase (PostgreSQL)
-- Version: 1.0
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE categories IS 'Product categories for inventory organization';

-- ============================================
-- PRODUCTS TABLE
-- ============================================
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    cost_price DECIMAL(10,2) CHECK (cost_price >= 0),
    current_stock INTEGER DEFAULT 0 CHECK (current_stock >= 0),
    min_stock_level INTEGER DEFAULT 5 CHECK (min_stock_level >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Main products inventory table';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit - unique product identifier';
COMMENT ON COLUMN products.min_stock_level IS 'Threshold for low stock alerts';

-- Indexes for product search and filtering
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_low_stock ON products(current_stock, min_stock_level) 
    WHERE current_stock <= min_stock_level AND is_active = TRUE;

-- ============================================
-- INVENTORY MOVEMENTS TABLE
-- ============================================
CREATE TYPE movement_type AS ENUM ('ENTRY', 'EXIT', 'ADJUSTMENT');
CREATE TYPE movement_reason AS ENUM ('PURCHASE', 'SALE', 'RETURN', 'DAMAGE', 'CORRECTION', 'OTHER');

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    movement_type movement_type NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    reason movement_reason NOT NULL,
    reference_id UUID,
    notes TEXT,
    previous_stock INTEGER NOT NULL,
    new_stock INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

COMMENT ON TABLE inventory_movements IS 'Audit trail for all inventory changes';
COMMENT ON COLUMN inventory_movements.reference_id IS 'Reference to related sale or purchase order';

CREATE INDEX idx_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_movements_date ON inventory_movements(created_at DESC);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type);

-- ============================================
-- SALES TABLE
-- ============================================
CREATE TYPE sale_status AS ENUM ('COMPLETED', 'CANCELLED');

CREATE TABLE sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_number VARCHAR(20) NOT NULL UNIQUE,
    sale_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
    discount DECIMAL(10,2) DEFAULT 0 CHECK (discount >= 0),
    tax DECIMAL(10,2) DEFAULT 0 CHECK (tax >= 0),
    total DECIMAL(10,2) NOT NULL CHECK (total >= 0),
    status sale_status DEFAULT 'COMPLETED',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

COMMENT ON TABLE sales IS 'Sales transactions header';

CREATE INDEX idx_sales_date ON sales(sale_date DESC);
CREATE INDEX idx_sales_number ON sales(sale_number);
CREATE INDEX idx_sales_status ON sales(status);

-- ============================================
-- SALE ITEMS TABLE
-- ============================================
CREATE TABLE sale_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    discount DECIMAL(10,2) DEFAULT 0 CHECK (discount >= 0),
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0)
);

COMMENT ON TABLE sale_items IS 'Individual line items for each sale';

CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
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

-- Function to generate sale number
CREATE OR REPLACE FUNCTION generate_sale_number()
RETURNS TRIGGER AS $$
DECLARE
    year_prefix VARCHAR(4);
    next_number INTEGER;
BEGIN
    year_prefix := TO_CHAR(NOW(), 'YYYY');
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(sale_number FROM 6) AS INTEGER)), 0) + 1
    INTO next_number
    FROM sales
    WHERE sale_number LIKE year_prefix || '-%';
    
    NEW.sale_number := year_prefix || '-' || LPAD(next_number::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-generating sale numbers
CREATE TRIGGER trigger_generate_sale_number
    BEFORE INSERT ON sales
    FOR EACH ROW
    WHEN (NEW.sale_number IS NULL)
    EXECUTE FUNCTION generate_sale_number();

-- ============================================
-- VIEWS
-- ============================================

-- View for products with low stock
CREATE VIEW v_low_stock_products AS
SELECT 
    p.id,
    p.sku,
    p.name,
    c.name as category_name,
    p.current_stock,
    p.min_stock_level,
    (p.min_stock_level - p.current_stock) as units_needed
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.current_stock <= p.min_stock_level
    AND p.is_active = TRUE
ORDER BY (p.min_stock_level - p.current_stock) DESC;

-- View for daily sales summary
CREATE VIEW v_daily_sales_summary AS
SELECT 
    DATE(sale_date) as sale_day,
    COUNT(*) as total_transactions,
    SUM(subtotal) as gross_sales,
    SUM(discount) as total_discounts,
    SUM(tax) as total_tax,
    SUM(total) as net_sales
FROM sales
WHERE status = 'COMPLETED'
GROUP BY DATE(sale_date)
ORDER BY sale_day DESC;

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Uncomment to insert sample categories
/*
INSERT INTO categories (name, description) VALUES
    ('Beverages', 'Drinks and refreshments'),
    ('Snacks', 'Chips, cookies, and quick bites'),
    ('Dairy', 'Milk, cheese, and dairy products'),
    ('Cleaning', 'Household cleaning supplies'),
    ('Personal Care', 'Hygiene and personal care items');
*/

-- ============================================
-- ROW LEVEL SECURITY (Optional - for multi-user)
-- ============================================

-- Enable RLS on tables (uncomment when implementing auth)
/*
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE sale_items ENABLE ROW LEVEL SECURITY;
*/

