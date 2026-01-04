-- ============================================
-- Comercial Comarapa - Database Schema
-- Database: Supabase (PostgreSQL)
-- Version: 2.1 (Refined Search)
-- ============================================

-- ============================================
-- EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent; -- Added for accent-insensitive search

-- Wrapper for unaccent to make it IMMUTABLE for use in GENERATED columns
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text AS $$
    SELECT unaccent($1);
$$ LANGUAGE sql IMMUTABLE;

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- PRODUCTS TABLE
-- ============================================
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    category_name VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    cost_price DECIMAL(10,2) CHECK (cost_price >= 0),
    current_stock INTEGER DEFAULT 0 CHECK (current_stock >= 0),
    min_stock_level INTEGER DEFAULT 5 CHECK (min_stock_level >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Improved search_vector with immutable_unaccent for better matching
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('spanish', immutable_unaccent(coalesce(name, ''))), 'A') ||
        setweight(to_tsvector('spanish', immutable_unaccent(coalesce(sku, ''))), 'A') ||
        setweight(to_tsvector('spanish', immutable_unaccent(coalesce(category_name, ''))), 'B') ||
        setweight(to_tsvector('spanish', immutable_unaccent(coalesce(description, ''))), 'C')
    ) STORED
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_products_search_vector ON products USING GIN(search_vector);
CREATE INDEX idx_products_name_trgm ON products USING GIN(immutable_unaccent(name) gin_trgm_ops);
CREATE INDEX idx_products_sku_trgm ON products USING GIN(immutable_unaccent(sku) gin_trgm_ops);
CREATE INDEX idx_products_category_name_trgm ON products USING GIN(immutable_unaccent(category_name) gin_trgm_ops);
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

CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);

-- ============================================
-- CORE TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Sync category_name (BEFORE to ensure search_vector consistency)
CREATE OR REPLACE FUNCTION sync_product_category_name()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.category_id IS DISTINCT FROM OLD.category_id OR TG_OP = 'INSERT' THEN
        IF NEW.category_id IS NOT NULL THEN
            SELECT name INTO NEW.category_name FROM categories WHERE id = NEW.category_id;
        ELSE
            NEW.category_name := NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_product_category_name
    BEFORE INSERT OR UPDATE OF category_id ON products
    FOR EACH ROW EXECUTE FUNCTION sync_product_category_name();

-- Update products on category name change
CREATE OR REPLACE FUNCTION sync_category_name_on_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.name IS DISTINCT FROM OLD.name THEN
        UPDATE products SET category_name = NEW.name WHERE category_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_category_name_on_update
    AFTER UPDATE OF name ON categories
    FOR EACH ROW EXECUTE FUNCTION sync_category_name_on_update();

-- ============================================
-- ENHANCED HYBRID SEARCH FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION search_products_hybrid(
    search_term TEXT,
    result_limit INTEGER DEFAULT 20,
    similarity_threshold DOUBLE PRECISION DEFAULT 0.3,
    is_active_filter BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    id UUID, sku VARCHAR(50), name VARCHAR(255), description TEXT,
    category_id UUID, category_name VARCHAR(100), unit_price DECIMAL(10,2),
    cost_price DECIMAL(10,2), current_stock INTEGER, min_stock_level INTEGER,
    is_active BOOLEAN, created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE, relevance FLOAT
) AS $$
DECLARE
    clean_term TEXT;
BEGIN
    -- Normalization: Trim and unaccent search term
    clean_term := immutable_unaccent(trim(search_term));
    
    -- Guard: Return empty if term is too short
    IF length(clean_term) < 1 THEN RETURN; END IF;

    RETURN QUERY
    SELECT 
        p.id, p.sku, p.name, p.description, p.category_id, p.category_name,
        p.unit_price, p.cost_price, p.current_stock, p.min_stock_level,
        p.is_active, p.created_at, p.updated_at,
        GREATEST(
            COALESCE(ts_rank_cd(p.search_vector, plainto_tsquery('spanish', clean_term)), 0) * 2,
            COALESCE(similarity(immutable_unaccent(p.name), clean_term), 0),
            COALESCE(similarity(immutable_unaccent(p.sku), clean_term), 0),
            COALESCE(similarity(immutable_unaccent(p.category_name), clean_term), 0) * 0.8,
            COALESCE(similarity(immutable_unaccent(p.description), clean_term), 0) * 0.5
        )::FLOAT AS relevance
    FROM products p
    WHERE 
        p.is_active = is_active_filter
        AND (
            p.search_vector @@ plainto_tsquery('spanish', clean_term)
            OR similarity(immutable_unaccent(p.name), clean_term) >= similarity_threshold
            OR similarity(immutable_unaccent(p.sku), clean_term) >= similarity_threshold
            OR similarity(immutable_unaccent(p.category_name), clean_term) >= similarity_threshold
            OR similarity(immutable_unaccent(p.description), clean_term) >= similarity_threshold
            OR immutable_unaccent(p.name) ILIKE '%' || clean_term || '%'
        )
    ORDER BY relevance DESC, p.name ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- VIEWS
-- ============================================

CREATE VIEW v_low_stock_products AS
SELECT 
    p.id, p.sku, p.name, c.name as category_name,
    p.current_stock, p.min_stock_level,
    (p.min_stock_level - p.current_stock) as units_needed
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.current_stock <= p.min_stock_level
    AND p.is_active = TRUE
ORDER BY (p.min_stock_level - p.current_stock) DESC;
