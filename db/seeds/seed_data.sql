-- ============================================
-- Comercial Comarapa - Seed Data
-- For development and testing purposes
-- ============================================

-- ============================================
-- CATEGORIES
-- ============================================
INSERT INTO categories (name, description) VALUES
    ('Bebidas', 'Refrescos, jugos, agua y bebidas en general'),
    ('Lacteos', 'Leche, queso, yogurt y derivados'),
    ('Abarrotes', 'Productos basicos: arroz, azucar, aceite, fideos'),
    ('Limpieza', 'Productos de limpieza del hogar'),
    ('Higiene Personal', 'Jabon, shampoo, pasta dental'),
    ('Snacks', 'Galletas, papas fritas, dulces'),
    ('Enlatados', 'Conservas, atun, sardinas'),
    ('Panaderia', 'Pan, facturas, galletas artesanales'),
    ('Carnes y Embutidos', 'Jamon, salchichas, mortadela'),
    ('Frutas y Verduras', 'Productos frescos');

-- ============================================
-- PRODUCTS
-- ============================================

-- Get category IDs (using subqueries for portability)
-- Bebidas
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('BEB-001', 'Coca Cola 2L', 'Gaseosa Coca Cola botella 2 litros', (SELECT id FROM categories WHERE name = 'Bebidas'), 15.00, 12.00, 48, 12),
    ('BEB-002', 'Pepsi 2L', 'Gaseosa Pepsi botella 2 litros', (SELECT id FROM categories WHERE name = 'Bebidas'), 14.50, 11.50, 36, 12),
    ('BEB-003', 'Agua Vital 1L', 'Agua mineral sin gas 1 litro', (SELECT id FROM categories WHERE name = 'Bebidas'), 5.00, 3.50, 100, 24),
    ('BEB-004', 'Jugo Tampico 1L', 'Jugo de naranja Tampico', (SELECT id FROM categories WHERE name = 'Bebidas'), 12.00, 9.00, 24, 10),
    ('BEB-005', 'Cerveza Pacena 620ml', 'Cerveza Pacena botella 620ml', (SELECT id FROM categories WHERE name = 'Bebidas'), 12.00, 9.50, 60, 24);

-- Lacteos
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('LAC-001', 'Leche PIL 1L', 'Leche entera PIL bolsa 1 litro', (SELECT id FROM categories WHERE name = 'Lacteos'), 8.50, 7.00, 50, 20),
    ('LAC-002', 'Yogurt Pil Frutilla 1L', 'Yogurt bebible sabor frutilla', (SELECT id FROM categories WHERE name = 'Lacteos'), 14.00, 11.00, 30, 10),
    ('LAC-003', 'Queso Criollo 1kg', 'Queso fresco criollo por kilo', (SELECT id FROM categories WHERE name = 'Lacteos'), 45.00, 38.00, 15, 5),
    ('LAC-004', 'Mantequilla PIL 200g', 'Mantequilla con sal', (SELECT id FROM categories WHERE name = 'Lacteos'), 18.00, 14.00, 20, 8);

-- Abarrotes
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('ABA-001', 'Arroz Grano de Oro 1kg', 'Arroz blanco premium', (SELECT id FROM categories WHERE name = 'Abarrotes'), 9.00, 7.00, 100, 30),
    ('ABA-002', 'Azucar San Aurelio 1kg', 'Azucar blanca refinada', (SELECT id FROM categories WHERE name = 'Abarrotes'), 8.00, 6.50, 80, 25),
    ('ABA-003', 'Aceite Fino 1L', 'Aceite vegetal de soya', (SELECT id FROM categories WHERE name = 'Abarrotes'), 16.00, 13.00, 45, 15),
    ('ABA-004', 'Fideo Carozzi 400g', 'Fideo spaghetti', (SELECT id FROM categories WHERE name = 'Abarrotes'), 7.00, 5.50, 60, 20),
    ('ABA-005', 'Sal Lobos 1kg', 'Sal de mesa yodada', (SELECT id FROM categories WHERE name = 'Abarrotes'), 3.00, 2.00, 40, 15),
    ('ABA-006', 'Harina Blancaflor 1kg', 'Harina de trigo con leudante', (SELECT id FROM categories WHERE name = 'Abarrotes'), 10.00, 8.00, 35, 10);

-- Limpieza
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('LIM-001', 'Detergente Omo 1kg', 'Detergente en polvo multiusos', (SELECT id FROM categories WHERE name = 'Limpieza'), 28.00, 22.00, 25, 10),
    ('LIM-002', 'Jabon Bolivar Barra', 'Jabon de lavar ropa', (SELECT id FROM categories WHERE name = 'Limpieza'), 6.00, 4.50, 50, 15),
    ('LIM-003', 'Cloro Clorox 1L', 'Blanqueador liquido', (SELECT id FROM categories WHERE name = 'Limpieza'), 12.00, 9.00, 30, 10),
    ('LIM-004', 'Lavavajillas Axion 500g', 'Jabon para platos', (SELECT id FROM categories WHERE name = 'Limpieza'), 15.00, 11.00, 20, 8);

-- Higiene Personal
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('HIG-001', 'Jabon Palmolive 3-pack', 'Jabon de tocador 3 unidades', (SELECT id FROM categories WHERE name = 'Higiene Personal'), 15.00, 11.00, 30, 10),
    ('HIG-002', 'Shampoo Head & Shoulders 400ml', 'Shampoo anticaspa', (SELECT id FROM categories WHERE name = 'Higiene Personal'), 35.00, 28.00, 15, 5),
    ('HIG-003', 'Pasta Dental Colgate 100ml', 'Pasta dental con fluor', (SELECT id FROM categories WHERE name = 'Higiene Personal'), 12.00, 9.00, 40, 15),
    ('HIG-004', 'Papel Higienico Elite 4-pack', 'Papel higienico doble hoja', (SELECT id FROM categories WHERE name = 'Higiene Personal'), 18.00, 14.00, 35, 12);

-- Snacks
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('SNK-001', 'Papas Lays Original 150g', 'Papas fritas clasicas', (SELECT id FROM categories WHERE name = 'Snacks'), 12.00, 9.00, 40, 15),
    ('SNK-002', 'Galletas Oreo 118g', 'Galletas rellenas de chocolate', (SELECT id FROM categories WHERE name = 'Snacks'), 10.00, 7.50, 50, 20),
    ('SNK-003', 'Chocolates Arcor Surtido', 'Bolsa de chocolates variados', (SELECT id FROM categories WHERE name = 'Snacks'), 25.00, 19.00, 20, 8),
    ('SNK-004', 'Mani Salado 200g', 'Mani tostado con sal', (SELECT id FROM categories WHERE name = 'Snacks'), 8.00, 6.00, 30, 10);

-- Enlatados
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('ENL-001', 'Atun Real 170g', 'Atun en aceite', (SELECT id FROM categories WHERE name = 'Enlatados'), 18.00, 14.00, 40, 15),
    ('ENL-002', 'Sardinas La Sirena 125g', 'Sardinas en salsa de tomate', (SELECT id FROM categories WHERE name = 'Enlatados'), 10.00, 7.50, 35, 12),
    ('ENL-003', 'Duraznos en Almibar 820g', 'Duraznos en conserva', (SELECT id FROM categories WHERE name = 'Enlatados'), 22.00, 17.00, 20, 8);

-- Carnes y Embutidos
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('CAR-001', 'Jamon Cocido 200g', 'Jamon de cerdo rebanado', (SELECT id FROM categories WHERE name = 'Carnes y Embutidos'), 25.00, 20.00, 15, 5),
    ('CAR-002', 'Salchichas Sofía 500g', 'Salchichas de pollo', (SELECT id FROM categories WHERE name = 'Carnes y Embutidos'), 22.00, 17.00, 20, 8),
    ('CAR-003', 'Mortadela 300g', 'Mortadela de cerdo', (SELECT id FROM categories WHERE name = 'Carnes y Embutidos'), 18.00, 14.00, 12, 5);

-- ============================================
-- LOW STOCK PRODUCTS (for testing alerts)
-- ============================================
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('BEB-006', 'Sprite 2L', 'Gaseosa Sprite lima limon', (SELECT id FROM categories WHERE name = 'Bebidas'), 14.00, 11.00, 3, 10),
    ('ABA-007', 'Cafe Nescafe 50g', 'Cafe instantaneo', (SELECT id FROM categories WHERE name = 'Abarrotes'), 25.00, 20.00, 2, 8);

-- ============================================
-- SAMPLE INVENTORY MOVEMENTS
-- ============================================

-- Initial stock entries for some products
INSERT INTO inventory_movements (product_id, movement_type, quantity, reason, notes, previous_stock, new_stock)
SELECT 
    id,
    'ENTRY'::movement_type,
    current_stock,
    'PURCHASE'::movement_reason,
    'Stock inicial de apertura',
    0,
    current_stock
FROM products
LIMIT 10;

-- ============================================
-- SAMPLE SALES (for testing)
-- ============================================

-- Sale 1
INSERT INTO sales (subtotal, discount, tax, total, notes) VALUES
    (85.50, 5.00, 0, 80.50, 'Venta de prueba 1');

-- Get the sale ID and insert items
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, subtotal)
SELECT 
    (SELECT id FROM sales ORDER BY created_at DESC LIMIT 1),
    p.id,
    2,
    p.unit_price,
    0,
    p.unit_price * 2
FROM products p
WHERE p.sku IN ('BEB-001', 'LAC-001', 'ABA-001')
LIMIT 3;

-- Sale 2
INSERT INTO sales (subtotal, discount, tax, total, notes) VALUES
    (120.00, 0, 0, 120.00, 'Venta de prueba 2');

INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, subtotal)
SELECT 
    (SELECT id FROM sales ORDER BY created_at DESC LIMIT 1),
    p.id,
    1,
    p.unit_price,
    0,
    p.unit_price
FROM products p
WHERE p.sku IN ('HIG-002', 'SNK-001', 'ENL-001')
LIMIT 3;

-- ============================================
-- VERIFY DATA
-- ============================================
-- Run these queries to verify:
-- SELECT COUNT(*) FROM categories;  -- Should be 10
-- SELECT COUNT(*) FROM products;    -- Should be ~30
-- SELECT COUNT(*) FROM sales;       -- Should be 2
-- SELECT * FROM v_low_stock_products;  -- Should show 2 products



