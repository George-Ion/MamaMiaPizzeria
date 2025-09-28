-- Sample Data for Mamma Mia Pizza Database

-- 1. User table (10 records - mix of customers, staff, admin)
INSERT INTO `User` (first_name, last_name, email, phone, date_of_birth, address, postal_code, user_type) VALUES
('Marco', 'Rossi', 'marco.rossi@email.com', '+39 331 1234567', '1985-03-15', 'Via Roma 123, Milano', '20121', 'Customer'),
('Sofia', 'Bianchi', 'sofia.bianchi@email.com', '+39 347 2345678', '1992-07-22', 'Corso Venezia 45, Milano', '20122', 'Customer'),
('Giuseppe', 'Ferrari', 'giuseppe.ferrari@email.com', '+39 339 3456789', '1978-11-08', 'Piazza Duomo 8, Milano', '20123', 'Staff'),
('Elena', 'Romano', 'elena.romano@email.com', '+39 338 4567890', '1995-09-14', 'Via Montenapoleone 67, Milano', '20121', 'Customer'),
('Antonio', 'Conti', 'antonio.conti@email.com', '+39 349 5678901', '1988-02-28', 'Viale Papiniano 12, Milano', '20123', 'Staff'),
('Giulia', 'Martini', 'giulia.martini@email.com', '+39 333 6789012', '1990-12-03', 'Via Brera 33, Milano', '20121', 'Customer'),
('Francesco', 'De Luca', 'francesco.deluca@email.com', '+39 340 7890123', '1983-06-17', 'Corso Buenos Aires 88, Milano', '20124', 'Staff'),
('Chiara', 'Galli', 'chiara.galli@email.com', '+39 334 8901234', '1996-04-11', 'Via Torino 156, Milano', '20123', 'Customer'),
('Matteo', 'Ricci', 'matteo.ricci@email.com', '+39 345 9012345', '1987-10-25', 'Navigli District 22, Milano', '20144', 'Customer'),
('Francesca', 'Greco', 'francesca.greco@email.com', '+39 329 0123456', '1975-01-12', 'Via Garibaldi 77, Milano', '20121', 'Admin');

-- 2. Customer table (7 customers from User table)
INSERT INTO Customer (total_pizzas_ordered, user_id) VALUES
(3, 1),   -- Marco Rossi
(7, 2),   -- Sofia Bianchi  
(12, 4),  -- Elena Romano (eligible for 10% discount)
(2, 6),   -- Giulia Martini
(15, 8),  -- Chiara Galli (eligible for 10% discount)
(8, 9),   -- Matteo Ricci
(1, 10);  -- Francesca Greco (admin but also customer)

-- 3. Staff table (3 staff from User table)
INSERT INTO Staff (last_delivery_time, is_available, user_id) VALUES
('2024-01-15 14:30:00', TRUE, 3),   -- Giuseppe Ferrari
('2024-01-15 15:45:00', FALSE, 5),  -- Antonio Conti (unavailable)
('2024-01-15 13:20:00', TRUE, 7);   -- Francesco De Luca

-- 4. Ingredients table (10 ingredients)
INSERT INTO ingredients (name, cost_per_unit, category) VALUES
('Mozzarella di Bufala', 2.50, 'Dairy'),
('Pomodori San Marzano', 1.20, 'Vegetable'),
('Prosciutto di Parma', 4.80, 'Meat'),
('Basilico Fresco', 0.80, 'Vegetable'),
('Funghi Porcini', 3.20, 'Vegetable'),
('Salame Piccante', 2.90, 'Meat'),
('Olive Nere di Gaeta', 1.60, 'Vegetable'),
('Gorgonzola DOP', 3.10, 'Dairy'),
('Rucola', 1.40, 'Vegetable'),
('Olio Extra Vergine', 0.95, 'Other');

-- 5. Pizzas table (10 classic Italian pizzas)
INSERT INTO pizzas (name, description) VALUES
('Margherita', 'La classica pizza con pomodoro, mozzarella e basilico'),
('Marinara', 'Pomodoro, aglio, origano e olio extra vergine'),
('Prosciutto e Funghi', 'Pomodoro, mozzarella, prosciutto cotto e funghi champignon'),
('Quattro Stagioni', 'Pomodoro, mozzarella, prosciutto, funghi, carciofi e olive'),
('Diavola', 'Pomodoro, mozzarella e salame piccante'),
('Capricciosa', 'Pomodoro, mozzarella, prosciutto, funghi, carciofi, olive e uovo'),
('Quattro Formaggi', 'Mozzarella, gorgonzola, parmigiano e fontina'),
('Prosciutto di Parma', 'Pomodoro, mozzarella, prosciutto di Parma e rucola'),
('Funghi Porcini', 'Pomodoro, mozzarella e funghi porcini'),
('Vegetariana', 'Pomodoro, mozzarella, zucchine, melanzane, peperoni e rucola');

-- 6. Pizza_ingredients table (ingredients for each pizza)
-- Margherita
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(1, 2), -- Pomodori San Marzano (grams)
(1, 1), -- Mozzarella di Bufala
(1, 4),  -- Basilico Fresco
(1, 10); -- Olio Extra Vergine

-- Marinara (basic but delicious)
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(2, 2), -- Pomodori San Marzano
(2, 4), -- Basilico Fresco
(2, 10); -- Olio Extra Vergine

-- Prosciutto di Parma
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(8, 2), -- Pomodori San Marzano
(8, 1), -- Mozzarella di Bufala
(8, 3), -- Prosciutto di Parma
(8, 9); -- Rucola

-- Diavola
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(5, 2), -- Pomodori San Marzano
(5, 1), -- Mozzarella di Bufala
(5, 6);  -- Salame Piccante

-- Quattro Formaggi
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(7, 1),  -- Mozzarella di Bufala
(7, 8);  -- Gorgonzola DOP

-- Funghi Porcini
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(9, 2), -- Pomodori San Marzano
(9, 1), -- Mozzarella di Bufala
(9, 5); -- Funghi Porcini

-- Prosciutto e Funghi
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(3, 2), -- Pomodori San Marzano
(3, 1), -- Mozzarella di Bufala
(3, 3), -- Prosciutto
(3, 5); -- Funghi

-- Quattro Stagioni
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(4, 2), -- Pomodori San Marzano
(4, 1), -- Mozzarella di Bufala
(4, 3), -- Prosciutto
(4, 5), -- Funghi
(4, 7); -- Olive

-- Capricciosa
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(6, 2), -- Pomodori San Marzano
(6, 1), -- Mozzarella di Bufala
(6, 3), -- Prosciutto
(6, 5), -- Funghi
(6, 7); -- Olive

-- Vegetariana
INSERT INTO pizza_ingredients (pizza_id, ingredient_id) VALUES
(10, 2), -- Pomodori San Marzano
(10, 1), -- Mozzarella di Bufala
(10, 4), -- Basilico
(10, 5), -- Funghi
(10, 7), -- Olive
(10, 9); -- Rucola

INSERT INTO drinks (name, price) VALUES
('Coca-Cola 33cl', 2.50),
('Acqua Naturale San Pellegrino 50cl', 2.00),
('Acqua Frizzante San Pellegrino 50cl', 2.00),
('Birra Peroni 33cl', 3.50),
('Birra Nastro Azzurro 33cl', 3.80),
('Vino Chianti Classico (bicchiere)', 4.50),
('Spremuta Arancia Fresca', 3.20),
('Caffè Espresso', 1.50),
('Limoncello', 3.80),
('Aranciata San Pellegrino 33cl', 2.80);

-- 8. Desserts table (10 Italian desserts)
INSERT INTO desserts (name, price) VALUES
('Tiramisù della Casa', 5.50),
('Panna Cotta ai Frutti di Bosco', 4.80),
('Cannoli Siciliani (2 pezzi)', 5.20),
('Gelato Artigianale (3 gusti)', 4.50),
('Torta della Nonna', 4.20),
('Affogato al Caffè', 3.80),
('Millefoglie alla Crema', 5.80),
('Sorbetto al Limone', 3.50),
('Biscotti della Fortuna', 2.80),
('Semifreddo al Pistacchio', 6.20);

-- 9. Orders table (10 orders)
INSERT INTO Orders (customer_id, staff_id, delivery_status, created_at, discount_amount, final_total) VALUES
(1, 1, 'Delivered', '2024-01-10 19:30:00', 0.00, 28.50),
(2, 2, 'Delivered', '2024-01-12 20:15:00', 0.00, 31.20),
(3, 1, 'Out for Delivery', '2024-01-15 18:45:00', 2.80, 25.00),
(4, 3, 'Pending', '2024-01-15 19:20:00', 0.00, 22.40),
(5, 1, 'In Progress', '2024-01-15 19:45:00', 1.50, 13.20),
(2, 2, 'Delivered', '2024-01-14 20:30:00', 0.00, 35.80),
(6, 3, 'Delivered', '2024-01-13 18:20:00', 0.00, 27.90),
(1, 1, 'Cancelled', '2024-01-11 21:00:00', 0.00, 0.00),
(4, 2, 'Delivered', '2024-01-09 19:15:00', 0.00, 33.60),
(3, 3, 'Pending', '2024-01-15 20:10:00', 3.20, 28.80);

-- 10. Order_Item table (items for the orders)
INSERT INTO Order_Item (order_id, item_type, pizza_id, drink_id, dessert_id, quantity, total_price) VALUES
-- Order 1: Marco's order
(1, 'Pizza', 1, NULL, NULL, 2, 22.00),
(1, 'Drink', NULL, 1, NULL, 2, 5.00),
(1, 'Dessert', NULL, NULL, 1, 1, 5.50),

-- Order 2: Sofia's order
(2, 'Pizza', 8, NULL, NULL, 1, 15.80),
(2, 'Pizza', 5, NULL, NULL, 1, 13.20),
(2, 'Drink', NULL, 4, NULL, 1, 3.50),

-- Order 3: Elena's order (with discount)
(3, 'Pizza', 7, NULL, NULL, 1, 14.60),
(3, 'Pizza', 9, NULL, NULL, 1, 16.20),
(3, 'Drink', NULL, 2, NULL, 2, 4.00),

-- Order 4: Giulia's order
(4, 'Pizza', 1, NULL, NULL, 1, 11.00),
(4, 'Drink', NULL, 3, NULL, 1, 2.00),
(4, 'Dessert', NULL, NULL, 4, 2, 9.00);

-- 11. Discount_Code table (10 discount codes)
INSERT INTO Discount_Code (code_name, discount_value, is_used, expiry_date) VALUES
('WELCOME10', 10.00, FALSE, '2024-12-31'),
('PIZZA20', 20.00, TRUE, '2024-06-30'),
('SUMMER15', 15.00, FALSE, '2024-08-31'),
('STUDENT5', 5.00, FALSE, '2024-12-31'),
('FAMIGLIA25', 25.00, FALSE, '2024-07-31'),
('WEEKEND12', 12.00, TRUE, '2024-03-31'),
('LOYALTY30', 30.00, FALSE, '2024-09-30'),
('HAPPY18', 18.00, FALSE, '2024-05-31'),
('MAMMA50', 50.00, FALSE, '2024-04-30'),
('AMICI8', 8.00, TRUE, '2024-02-29');

-- 12. Order_Discount table (some orders with discounts applied)
INSERT INTO Order_Discount (order_id, code_id, discount_type, discount_amount) VALUES
(3, 7, 'FixedAmount', 2.80),  -- Elena's order with LOYALTY30
(5, 4, 'FixedAmount', 1.50),  -- Chiara's order with STUDENT5
(10, 8, 'Percentage', 3.20);  -- Elena's second order with HAPPY18

-- 13. Transaction table (transactions for completed orders)
INSERT INTO Transaction (order_id, transaction_amount, transaction_status, payment_method, transaction_date) VALUES
(1, 28.50, 'Paid', 'Card', '2024-01-10 19:35:00'),
(2, 31.20, 'Paid', 'Cash', '2024-01-12 20:20:00'),
(3, 25.00, 'Paid', 'Online', '2024-01-15 18:50:00'),
(4, 22.40, 'Pending', 'Card', '2024-01-15 19:25:00'),
(5, 13.20, 'Pending', 'Cash', '2024-01-15 19:50:00'),
(6, 35.80, 'Paid', 'Online', '2024-01-14 20:35:00'),
(7, 27.90, 'Paid', 'Card', '2024-01-13 18:25:00'),
(8, 0.00, 'Refunded', 'Card', '2024-01-11 21:05:00'),
(9, 33.60, 'Paid', 'Cash', '2024-01-09 19:20:00'),
(10, 28.80, 'Pending', 'Online', '2024-01-15 20:15:00');