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
    ('Frutas y Verduras', 'Productos frescos'),
    ('Lubricantes y Automotriz', 'Aceites, grasas, repuestos y accesorios para vehiculos'),
    ('Ferreteria', 'Herramientas, clavos, tornillos y materiales de construccion'),
    ('Pinturas y Aerosoles', 'Pinturas en spray, esmaltes y recubrimientos'),
    ('Herramientas Agricolas', 'Hachas, hoces, palas y herramientas de campo'),
    ('Electronicos y Electricidad', 'Linternas, cables, baterias y accesorios electricos'),
    ('Mangueras y Riego', 'Mangueras, aspersores y sistemas de riego'),
    ('Colchones y Hogar', 'Colchones, almohadas y articulos para el hogar'),
    ('Bicicletas y Deportes', 'Bicicletas, repuestos y articulos deportivos'),
    ('Calzado', 'Zapatos, botas de trabajo y calzado en general');

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
-- PRODUCTOS NUEVOS - Importados de Facturas
-- ============================================

-- Limpieza (nuevos productos)
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('LIM-005', 'Mopa Colores', 'Mopa de microfibra multicolor para limpieza de pisos y superficies', (SELECT id FROM categories WHERE name = 'Limpieza'), 40.00, 32.00, 24, 10),
    ('LIM-006', 'Basurera Max Grande', 'Basurera plastica tamano grande con tapa resistente', (SELECT id FROM categories WHERE name = 'Limpieza'), 50.00, 40.00, 12, 5),
    ('LIM-007', 'Papelera Grande', 'Papelera de plastico resistente capacidad grande para oficina o hogar', (SELECT id FROM categories WHERE name = 'Limpieza'), 60.00, 48.00, 12, 5),
    ('LIM-008', 'Papelera Color #20', 'Papelera plastica mediana tamano #20 varios colores disponibles', (SELECT id FROM categories WHERE name = 'Limpieza'), 40.00, 32.00, 24, 10),
    ('LIM-009', 'Caja Euroam', 'Caja organizadora Euroam para almacenamiento de articulos varios', (SELECT id FROM categories WHERE name = 'Limpieza'), 270.00, 216.00, 6, 3);

-- Lubricantes y Automotriz
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('AUT-001', 'Gato Hidraulico', 'Gato hidraulico de botella para levantamiento de vehiculos', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 285.00, 228.00, 6, 3),
    ('AUT-002', 'Silicon Vertex Grande', 'Silicon lubricante Vertex presentacion grande multiusos', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 32.50, 26.00, 24, 10),
    ('AUT-003', 'Paquete Destilado', 'Agua destilada para baterias y sistemas de enfriamiento', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 45.00, 36.00, 12, 5),
    ('AUT-004', 'Camara Gris', 'Camara de llanta color gris para bicicletas y motos', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 90.00, 72.00, 20, 8),
    ('AUT-005', 'Caja Aceite 20/50x1', 'Caja de aceite de motor 20W50 presentacion de 1 litro', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 380.00, 304.00, 6, 3),
    ('AUT-006', 'Borne Plomo', 'Borne de plomo para conexion de bateria automotriz', (SELECT id FROM categories WHERE name = 'Lubricantes y Automotriz'), 7.50, 6.00, 48, 20);

-- Ferreteria
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('FER-001', 'Espatula Metalica', 'Espatula metalica para trabajo de construccion y pintura', (SELECT id FROM categories WHERE name = 'Ferreteria'), 30.00, 24.00, 24, 10),
    ('FER-002', 'Caja Grampa', 'Caja de grampas metalicas para cercado y sujecion', (SELECT id FROM categories WHERE name = 'Ferreteria'), 43.00, 34.40, 20, 8),
    ('FER-003', 'Clavo 1.5 pulgada', 'Clavos de acero de 1.5 pulgada para construccion por quintal', (SELECT id FROM categories WHERE name = 'Ferreteria'), 28.00, 22.40, 10, 5),
    ('FER-004', 'Soga 1/4', 'Soga de nylon trenzada diametro 1/4 pulgada resistente por metro', (SELECT id FROM categories WHERE name = 'Ferreteria'), 1.18, 0.94, 200, 50),
    ('FER-005', 'Soga 5/16', 'Soga de nylon trenzada diametro 5/16 pulgada uso general por metro', (SELECT id FROM categories WHERE name = 'Ferreteria'), 3.40, 2.72, 150, 40),
    ('FER-006', 'Soga 3/8', 'Soga de nylon trenzada diametro 3/8 pulgada alta resistencia por metro', (SELECT id FROM categories WHERE name = 'Ferreteria'), 3.05, 2.44, 150, 40),
    ('FER-007', 'Soga 1/2', 'Soga de nylon trenzada diametro 1/2 pulgada uso pesado por metro', (SELECT id FROM categories WHERE name = 'Ferreteria'), 5.40, 4.32, 100, 30),
    ('FER-008', 'Disco Diamante 7 pulgadas', 'Disco de corte diamantado 7 pulgadas para amoladora', (SELECT id FROM categories WHERE name = 'Ferreteria'), 38.00, 30.40, 15, 6);

-- Pinturas y Aerosoles
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('PIN-001', 'Spray Blanco', 'Pintura en aerosol color blanco brillante secado rapido', (SELECT id FROM categories WHERE name = 'Pinturas y Aerosoles'), 180.00, 144.00, 12, 5);

-- Herramientas Agricolas
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('AGR-001', 'Hacha Pesada Formato', 'Hacha de trabajo pesado con mango de madera formato estandar', (SELECT id FROM categories WHERE name = 'Herramientas Agricolas'), 120.00, 96.00, 12, 5),
    ('AGR-002', 'Paletas Castner', 'Paleta de jardineria marca Castner para trasplante y siembra', (SELECT id FROM categories WHERE name = 'Herramientas Agricolas'), 50.00, 40.00, 18, 8),
    ('AGR-003', 'Hoces Atocha', 'Hoz de corte marca Atocha para cosecha y limpieza agricola', (SELECT id FROM categories WHERE name = 'Herramientas Agricolas'), 65.00, 52.00, 15, 6),
    ('AGR-004', 'Escofinas Modelo 10', 'Escofina modelo 10 para trabajo en madera y metal', (SELECT id FROM categories WHERE name = 'Herramientas Agricolas'), 70.00, 56.00, 12, 5);

-- Electronicos y Electricidad
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('ELE-001', 'Radio Cuba', 'Radio portatil Cuba con AM/FM recargable y linterna integrada', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 419.00, 335.20, 6, 3),
    ('ELE-002', 'Bateria Energizer', 'Bateria alcalina Energizer de larga duracion AA/AAA', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 20.00, 16.00, 60, 24),
    ('ELE-003', 'Brocha Electronica', 'Brocha para limpieza de equipos electronicos antiestatica', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 30.00, 24.00, 20, 8),
    ('ELE-004', 'Linterna Shur Chico', 'Linterna LED Shur tamano chico portatil con pilas', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 28.00, 22.40, 24, 10),
    ('ELE-005', 'Linterna Modelo 1341', 'Linterna LED modelo 1341 recargable alta luminosidad', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 45.00, 36.00, 18, 8),
    ('ELE-006', 'Linterna Modelo 1348', 'Linterna LED modelo 1348 compacta uso domestico', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 38.00, 30.40, 24, 10),
    ('ELE-007', 'Linterna Modelo 1346', 'Linterna LED modelo 1346 economica pilas incluidas', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 30.00, 24.00, 30, 12),
    ('ELE-008', 'Raqueta Mata Mosquitos Chica', 'Raqueta electrica mata mosquitos tamano chico recargable', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 40.00, 32.00, 18, 8),
    ('ELE-009', 'Raqueta Mata Mosquitos Grande', 'Raqueta electrica mata mosquitos tamano grande mayor cobertura', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 54.00, 43.20, 15, 6),
    ('ELE-010', 'Motor Amarillo', 'Motor electrico pequeno amarillo para proyectos y reparaciones', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 90.00, 72.00, 10, 4),
    ('ELE-011', 'Cable LG-651S', 'Cable de datos LG-651S para carga y transferencia de datos', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 13.00, 10.40, 36, 15),
    ('ELE-012', 'Cable Tipo 4 Gerlex', 'Cable cargador Tipo 4 Gerlex compatible multiples dispositivos', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 7.00, 5.60, 48, 20),
    ('ELE-013', 'Cable USB Tipo C', 'Cable USB Tipo C NSu carga rapida para smartphones', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 4.00, 3.20, 60, 25),
    ('ELE-014', 'Cautin Soldador E1-D7720', 'Cautin soldador E1-D7720 Sorder para electronica 40W', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 80.00, 64.00, 8, 4),
    ('ELE-015', 'Auriculares Jeler DGA-10', 'Auriculares Jeler DGA-10 con microfono incorporado', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 7.00, 5.60, 30, 12),
    ('ELE-016', 'Parlante Alkata MA-X15', 'Parlante portatil Alkata MA-X15 bluetooth recargable', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 65.00, 52.00, 10, 4),
    ('ELE-017', 'Extension Electrica 10x10', 'Extension electrica 10 metros con 10 tomas multiples', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 42.00, 33.60, 12, 5),
    ('ELE-018', 'Extension Electrica 5M Pro', 'Extension electrica profesional 5 metros alta capacidad', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 204.00, 163.20, 6, 3),
    ('ELE-019', 'Lampara LED Ecolo', 'Lampara LED ecologica Doc Ecolo bajo consumo energetico', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 212.00, 169.60, 8, 4),
    ('ELE-020', 'Extension Electrica 10x5M', 'Extension electrica 5 metros con 10 tomas uso domestico', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 23.00, 18.40, 20, 8),
    ('ELE-021', 'Extension Electrica 12x10 Industrial', 'Extension electrica industrial 10 metros 12 tomas profesional', (SELECT id FROM categories WHERE name = 'Electronicos y Electricidad'), 360.00, 288.00, 4, 2);

-- Mangueras y Riego
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('RIE-001', 'Monio Victoria', 'Aspersor tipo monio Victoria para riego de jardines y cultivos', (SELECT id FROM categories WHERE name = 'Mangueras y Riego'), 300.00, 240.00, 8, 4),
    ('RIE-002', 'Manguera Gomitol', 'Manguera flexible Gomitol para riego uso agricola y domestico por metro', (SELECT id FROM categories WHERE name = 'Mangueras y Riego'), 6.20, 4.96, 200, 50);

-- Colchones y Hogar
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('HOG-001', 'Colchonado 24H', 'Colchon acolchado 24H de espuma para descanso y comodidad', (SELECT id FROM categories WHERE name = 'Colchones y Hogar'), 160.00, 128.00, 15, 5);

-- Bicicletas y Deportes
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('BIC-001', 'Cross U-Scot', 'Bicicleta Cross U-Scot todo terreno resistente para adultos', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 1300.00, 1040.00, 4, 2),
    ('BIC-002', 'FX Canasta Mujir', 'Bicicleta FX con canasta Mujir para uso urbano y paseo', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 1300.00, 1040.00, 3, 2),
    ('BIC-003', 'Bicicleta Aro 20 Mg con Case', 'Bicicleta aro 20 con marco Mg y estuche incluido para ninos', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 980.00, 784.00, 6, 3),
    ('BIC-004', 'Bicicleta Aro 20 Ry Clase', 'Bicicleta aro 20 linea Ry Clase economica para ninos', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 890.00, 712.00, 6, 3),
    ('BIC-005', 'Bicicleta Aro 16', 'Bicicleta infantil aro 16 con rueditas de apoyo incluidas', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 730.00, 584.00, 8, 4),
    ('BIC-006', 'Bicicleta Aro 12', 'Bicicleta para ninos pequenos aro 12 primer bicicleta ideal', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 620.00, 496.00, 6, 3),
    ('BIC-007', 'Bicicleta Cross Mg', 'Bicicleta Cross con marco de magnesio todo terreno resistente', (SELECT id FROM categories WHERE name = 'Bicicletas y Deportes'), 1315.00, 1052.00, 4, 2);

-- Calzado
INSERT INTO products (sku, name, description, category_id, unit_price, cost_price, current_stock, min_stock_level) VALUES
    ('CAL-001', 'Calzado Caki Negro T40', 'Calzado de trabajo estilo Caki color negro talla 40 resistente', (SELECT id FROM categories WHERE name = 'Calzado'), 108.00, 86.40, 6, 3),
    ('CAL-002', 'Calzado Caki Negro T41', 'Calzado de trabajo estilo Caki color negro talla 41 resistente', (SELECT id FROM categories WHERE name = 'Calzado'), 108.00, 86.40, 6, 3),
    ('CAL-003', 'Calzado Caki Negro T42', 'Calzado de trabajo estilo Caki color negro talla 42 resistente', (SELECT id FROM categories WHERE name = 'Calzado'), 108.00, 86.40, 6, 3),
    ('CAL-004', 'Bota Bata T40', 'Bota de trabajo tipo Bata talla 40 suela antideslizante', (SELECT id FROM categories WHERE name = 'Calzado'), 138.00, 110.40, 6, 3),
    ('CAL-005', 'Bota Bata T41', 'Bota de trabajo tipo Bata talla 41 suela antideslizante', (SELECT id FROM categories WHERE name = 'Calzado'), 138.00, 110.40, 6, 3),
    ('CAL-006', 'Bota Bata T42', 'Bota de trabajo tipo Bata talla 42 suela antideslizante', (SELECT id FROM categories WHERE name = 'Calzado'), 138.00, 110.40, 6, 3);

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
-- SELECT COUNT(*) FROM categories;  -- Should be 19
-- SELECT COUNT(*) FROM products;    -- Should be ~90
-- SELECT COUNT(*) FROM sales;       -- Should be 2
-- SELECT * FROM v_low_stock_products;  -- Should show 2 products



