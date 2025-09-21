USE mamma_mia_pizza;

--
-- USER
--
INSERT INTO User (first_name, last_name, email, phone, date_of_birth, address, postal_code, user_type)
VALUES 
('Alice', 'Johnson', 'alice.j@email.com', '555-1000', '1990-05-14', '123 Main St', '11111', 'Customer'),
('Bob', 'Smith', 'bob.s@email.com', '555-2000', '1985-09-30', '45 Market St', '22222', 'Customer'),
('Charlie', 'Brown', 'charlie.b@email.com', '555-3000', '1992-12-01', '67 Pine Ave', '33333', 'Staff'),
('Diana', 'Evans', 'diana.e@email.com', '555-4000', '1998-03-22', '89 Lake Rd', '44444', 'Staff'),
('Eve', 'Williams', 'eve.w@email.com', '555-5000', '1995-01-20', '12 River Rd', '55555', 'Admin');

--
-- CUSTOMER
--
INSERT INTO Customer (total_pizzas_ordered, user_id)
VALUES
(12, 1),
(5, 2),
(7, 3),
(0, 4),
(20, 5);

--
-- STAFF
--
INSERT INTO Staff (position, hourly_rate, is_available, is_delivery_person, user_id)
VALUES
('Chef', 15.50, TRUE, FALSE, 3),
('Driver', 12.00, TRUE, TRUE, 4),
('Cashier', 11.00, TRUE, FALSE, 5),
('Manager', 20.00, TRUE, FALSE, 3),
('Chef', 16.00, FALSE, FALSE, 4);

--
-- DISCOUNT CODE
--
INSERT INTO Discount_Code (code_name, discount_value, is_used, expiry_date)
VALUES
('WELCOME10', 10.00, FALSE, '2025-12-31'),
('FREEDRINK', 5.00, FALSE, '2025-06-30'),
('BIGSALE20', 20.00, TRUE, '2024-12-31'),
('LOYALTY15', 15.00, FALSE, '2026-01-01'),
('STUDENT5', 5.00, FALSE, '2025-09-30');

--
-- ORDERS
--
INSERT INTO Orders (customer_id, staff_id, delivery_status, discount_amount, final_total)
VALUES
(1, 1, 'Pending', 0.00, 25.00),
(2, 1, 'In Progress', 5.00, 18.00),
(3, 2, 'Out for Delivery', 0.00, 40.00),
(4, 2, 'Delivered', 10.00, 30.00),
(5, 3, 'Cancelled', 0.00, 0.00);

--
-- ORDER ITEM
--
INSERT INTO Order_Item (order_id, item_type, pizza_id, drink_id, dessert_id, quantity, total_price)
VALUES
(1, 'Pizza', 1, NULL, NULL, 2, 20.00),
(1, 'Drink', NULL, 1, NULL, 1, 5.00),
(2, 'Pizza', 2, NULL, NULL, 1, 15.00),
(3, 'Pizza', 3, NULL, NULL, 3, 36.00),
(4, 'Dessert', NULL, NULL, 1, 2, 8.00);

--
-- ORDER DISCOUNT
--
INSERT INTO Order_Discount (order_id, code_id, discount_type, discount_amount)
VALUES
(2, 1, 'FixedAmount', 5.00),
(3, 2, 'FixedAmount', 5.00),
(4, 4, 'Percentage', 10.00),
(5, 3, 'FixedAmount', 20.00),
(1, 5, 'Percentage', 2.50);

--
-- TRANSACTION
--
INSERT INTO Transaction (order_id, transaction_amount, transaction_status, payment_method)
VALUES
(1, 25.00, 'Paid', 'Card'),
(2, 18.00, 'Pending', 'Cash'),
(3, 40.00, 'Paid', 'Online'),
(4, 30.00, 'Refunded', 'Card'),
(5, 0.00, 'Failed', 'Cash');
