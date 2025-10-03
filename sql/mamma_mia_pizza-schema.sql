DROP DATABASE IF EXISTS mamma_mia_pizza;
CREATE DATABASE mamma_mia_pizza;
USE mamma_mia_pizza;

-- 1. User table
CREATE TABLE `User` (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    address VARCHAR(255),
    postal_code VARCHAR(20),
    user_type ENUM('Customer','Staff','Admin') NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customer table
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    total_pizzas_ordered INT DEFAULT 0,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

-- 3. Staff table
CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    last_delivery_time DATETIME DEFAULT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    assigned_postal_code VARCHAR(20),  -- Primary delivery area
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

-- 4. Ingredients table
CREATE TABLE ingredients (
    ingredient_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cost_per_unit DECIMAL(8,2) NOT NULL CHECK (cost_per_unit > 0),
    category ENUM('Meat', 'Dairy', 'Vegetable', 'Vegan', 'Other') NOT NULL DEFAULT 'Vegetable',
    is_vegetarian BOOLEAN GENERATED ALWAYS AS (
        category IN ('Vegetable', 'Dairy', 'Vegan', 'Other')
    ) STORED,
    is_vegan BOOLEAN GENERATED ALWAYS AS (
        category IN ('Vegan', 'Vegetable', 'Other')
    ) STORED
);

-- 5. Pizzas table
CREATE TABLE pizzas (
    pizza_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

-- 6. Pizza_ingredients table
CREATE TABLE pizza_ingredients (
    pizza_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    PRIMARY KEY (pizza_id, ingredient_id),
    FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

-- 7. Drinks table
CREATE TABLE drinks (
    drink_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(8,2) NOT NULL CHECK (price > 0)
);

-- 8. Desserts table
CREATE TABLE desserts (
    dessert_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(8,2) NOT NULL CHECK (price > 0)
);

-- 9. Orders table
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    staff_id INT,
    delivery_status ENUM('Pending','In Progress','Out for Delivery','Delivered','Cancelled') DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    discount_amount DECIMAL(6,2) DEFAULT 0.00,
    final_total DECIMAL(8,2),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id)
);

-- 10. Order_Item table
CREATE TABLE Order_Item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_type ENUM('Pizza','Drink','Dessert') NOT NULL,
    pizza_id INT,
    drink_id INT,
    dessert_id INT,
    quantity INT NOT NULL CHECK (quantity > 0),
    total_price DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id),
    FOREIGN KEY (drink_id) REFERENCES drinks(drink_id),
    FOREIGN KEY (dessert_id) REFERENCES desserts(dessert_id)
);

-- 11. Discount_Code table
CREATE TABLE Discount_Code (
    code_id INT AUTO_INCREMENT PRIMARY KEY,
    code_name VARCHAR(50) UNIQUE NOT NULL,
    discount_value DECIMAL(5,2),
    is_used BOOLEAN DEFAULT FALSE,
    expiry_date DATE NOT NULL
);

-- 12. Order_Discount table
CREATE TABLE Order_Discount (
    order_discount_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    code_id INT NOT NULL,
    discount_type ENUM('Percentage','FixedAmount','FreePizza','FreeDrink') NOT NULL,
    discount_amount DECIMAL(6,2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (code_id) REFERENCES Discount_Code(code_id)
);

-- 13. Transaction table
CREATE TABLE Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    transaction_amount DECIMAL(8,2) NOT NULL,
    transaction_status ENUM('Pending','Paid','Failed','Refunded') DEFAULT 'Pending',
    payment_method ENUM('Cash','Card','Online') NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);

-- ========================
-- VIEWS FOR DYNAMIC PRICING
-- ========================

-- View to calculate pizza prices dynamically
CREATE VIEW pizza_menu AS
SELECT 
    p.pizza_id,
    p.name,
    p.description,
    -- Calculate total ingredient cost
    ROUND(SUM(i.cost_per_unit), 2) as ingredient_cost,
    -- Add 40% margin and 9% VAT: cost * 1.40 * 1.09
    ROUND(SUM(i.cost_per_unit) * 1.40 * 1.09, 2) as price,
    -- Check if pizza is vegetarian (all ingredients must be vegetarian)
    CASE 
        WHEN MIN(i.is_vegetarian) = 1 THEN TRUE 
        ELSE FALSE 
    END as is_vegetarian,
    -- Check if pizza is vegan (all ingredients must be vegan)
    CASE 
        WHEN MIN(i.is_vegan) = 1 THEN TRUE 
        ELSE FALSE 
    END as is_vegan
FROM pizzas p
JOIN pizza_ingredients pi ON p.pizza_id = pi.pizza_id
JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
GROUP BY p.pizza_id, p.name, p.description;

-- View for order summary with customer info
CREATE VIEW order_summary AS
SELECT 
    o.order_id,
    o.created_at,
    o.delivery_status,
    o.final_total,
    o.discount_amount,
    CONCAT(u.first_name, ' ', u.last_name) as customer_name,
    u.address,
    u.postal_code,
    c.total_pizzas_ordered,
    CASE 
        WHEN c.total_pizzas_ordered >= 10 THEN TRUE 
        ELSE FALSE 
    END as is_loyalty_customer
FROM Orders o
JOIN Customer c ON o.customer_id = c.customer_id
JOIN `User` u ON c.user_id = u.user_id;

-- View for undelivered orders
CREATE VIEW undelivered_orders AS
SELECT 
    o.order_id,
    o.created_at,
    o.delivery_status,
    o.final_total,
    CONCAT(u.first_name, ' ', u.last_name) as customer_name,
    u.address,
    u.postal_code,
    u.phone,
    TIMESTAMPDIFF(MINUTE, o.created_at, NOW()) as minutes_since_order
FROM Orders o
JOIN Customer c ON o.customer_id = c.customer_id
JOIN `User` u ON c.user_id = u.user_id
WHERE o.delivery_status IN ('Pending', 'In Progress', 'Out for Delivery');

-- View for delivery staff assignments
CREATE VIEW delivery_staff_view AS
SELECT 
    s.staff_id,
    CONCAT(u.first_name, ' ', u.last_name) as staff_name,
    u.phone,
    s.assigned_postal_code,
    s.is_available,
    s.last_delivery_time,
    CASE 
        WHEN s.last_delivery_time IS NULL THEN 'Never delivered'
        WHEN TIMESTAMPDIFF(MINUTE, s.last_delivery_time, NOW()) >= 30 THEN 'Available'
        ELSE CONCAT('Unavailable for ', 30 - TIMESTAMPDIFF(MINUTE, s.last_delivery_time, NOW()), ' more minutes')
    END as availability_status
FROM Staff s
JOIN `User` u ON s.user_id = u.user_id
ORDER BY s.assigned_postal_code;

-- ========================
-- FUNCTIONS FOR PRICING AND BUSINESS LOGIC
-- ========================

-- Function to get pizza price by ID
DELIMITER //
CREATE FUNCTION get_pizza_price(pizza_id_param INT) 
RETURNS DECIMAL(8,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE pizza_price DECIMAL(8,2) DEFAULT 0.00;
    
    SELECT ROUND(SUM(i.cost_per_unit) * 1.40 * 1.09, 2)
    INTO pizza_price
    FROM pizza_ingredients pi
    JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
    WHERE pi.pizza_id = pizza_id_param;
    
    RETURN IFNULL(pizza_price, 0.00);
END //
DELIMITER ;

-- Function to get ingredient cost for a pizza
DELIMITER //
CREATE FUNCTION get_pizza_ingredient_cost(pizza_id_param INT) 
RETURNS DECIMAL(8,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE ingredient_cost DECIMAL(8,2) DEFAULT 0.00;
    
    SELECT ROUND(SUM(i.cost_per_unit), 2)
    INTO ingredient_cost
    FROM pizza_ingredients pi
    JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
    WHERE pi.pizza_id = pizza_id_param;
    
    RETURN IFNULL(ingredient_cost, 0.00);
END //
DELIMITER ;

-- Function to check if pizza is vegetarian
DELIMITER //
CREATE FUNCTION is_pizza_vegetarian(pizza_id_param INT) 
RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE is_veg BOOLEAN DEFAULT TRUE;
    DECLARE non_veg_count INT DEFAULT 0;
    
    SELECT COUNT(*)
    INTO non_veg_count
    FROM pizza_ingredients pi
    JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
    WHERE pi.pizza_id = pizza_id_param 
    AND i.is_vegetarian = FALSE;
    
    IF non_veg_count > 0 THEN
        SET is_veg = FALSE;
    END IF;
    
    RETURN is_veg;
END //
DELIMITER ;

-- Function to check if pizza is vegan
DELIMITER //
CREATE FUNCTION is_pizza_vegan(pizza_id_param INT) 
RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE is_veg BOOLEAN DEFAULT TRUE;
    DECLARE non_vegan_count INT DEFAULT 0;
    
    SELECT COUNT(*)
    INTO non_vegan_count
    FROM pizza_ingredients pi
    JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
    WHERE pi.pizza_id = pizza_id_param 
    AND i.is_vegan = FALSE;
    
    IF non_vegan_count > 0 THEN
        SET is_veg = FALSE;
    END IF;
    
    RETURN is_veg;
END //
DELIMITER ;

-- Function to calculate loyalty discount
DELIMITER //
CREATE FUNCTION calculate_loyalty_discount(customer_id_param INT, order_total DECIMAL(8,2)) 
RETURNS DECIMAL(8,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE discount DECIMAL(8,2) DEFAULT 0.00;
    DECLARE pizza_count INT DEFAULT 0;
    
    SELECT total_pizzas_ordered
    INTO pizza_count
    FROM Customer
    WHERE customer_id = customer_id_param;
    
    IF pizza_count >= 10 THEN
        SET discount = ROUND(order_total * 0.10, 2);
    END IF;
    
    RETURN discount;
END //
DELIMITER ;

-- Function to check if today is customer's birthday
DELIMITER //
CREATE FUNCTION is_customer_birthday(customer_id_param INT) 
RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE is_birthday BOOLEAN DEFAULT FALSE;
    DECLARE birth_month INT;
    DECLARE birth_day INT;
    
    SELECT MONTH(u.date_of_birth), DAY(u.date_of_birth)
    INTO birth_month, birth_day
    FROM Customer c
    JOIN `User` u ON c.user_id = u.user_id
    WHERE c.customer_id = customer_id_param;
    
    IF birth_month = MONTH(CURDATE()) AND birth_day = DAY(CURDATE()) THEN
        SET is_birthday = TRUE;
    END IF;
    
    RETURN is_birthday;
END //
DELIMITER ;

-- ========================
-- STORED PROCEDURES FOR COMPLEX OPERATIONS
-- ========================

-- Procedure to place an order with transaction handling
DELIMITER //
CREATE PROCEDURE place_order(
    IN p_customer_id INT,
    IN p_discount_code VARCHAR(50),
    OUT p_order_id INT,
    OUT p_final_total DECIMAL(8,2),
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_subtotal DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_discount DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_loyalty_discount DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_code_discount DECIMAL(8,2) DEFAULT 0.00;
    DECLARE v_code_id INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: Order placement failed';
        SET p_order_id = 0;
        SET p_final_total = 0.00;
    END;
    
    START TRANSACTION;
    
    -- Create the order
    INSERT INTO Orders (customer_id, delivery_status, created_at)
    VALUES (p_customer_id, 'Pending', NOW());
    
    SET p_order_id = LAST_INSERT_ID();
    
    -- Calculate loyalty discount
    SET v_loyalty_discount = calculate_loyalty_discount(p_customer_id, v_subtotal);
    SET v_discount = v_discount + v_loyalty_discount;
    
    -- Apply discount code if provided
    IF p_discount_code IS NOT NULL AND p_discount_code != '' THEN
        SELECT code_id, discount_value 
        INTO v_code_id, v_code_discount
        FROM Discount_Code 
        WHERE code_name = p_discount_code 
        AND is_used = FALSE 
        AND expiry_date >= CURDATE()
        LIMIT 1;
        
        IF v_code_id IS NOT NULL THEN
            SET v_discount = v_discount + v_code_discount;
            UPDATE Discount_Code SET is_used = TRUE WHERE code_id = v_code_id;
        END IF;
    END IF;
    
    -- Calculate final total
    SET p_final_total = v_subtotal - v_discount;
    
    -- Update order with totals
    UPDATE Orders 
    SET discount_amount = v_discount, final_total = p_final_total
    WHERE order_id = p_order_id;
    
    COMMIT;
    SET p_status = 'SUCCESS: Order placed successfully';
END //
DELIMITER ;

-- Procedure to assign delivery driver
DELIMITER //
CREATE PROCEDURE assign_delivery_driver(
    IN p_order_id INT,
    IN p_postal_code VARCHAR(20),
    OUT p_staff_id INT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_available_staff INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR: Driver assignment failed';
        SET p_staff_id = 0;
    END;
    
    START TRANSACTION;
    
    -- Find available staff assigned to the postal code area
    SELECT s.staff_id
    INTO v_available_staff
    FROM Staff s
    WHERE s.is_available = TRUE
    AND (s.last_delivery_time IS NULL 
         OR TIMESTAMPDIFF(MINUTE, s.last_delivery_time, NOW()) >= 30)
    AND s.assigned_postal_code = p_postal_code
    LIMIT 1;
    
    IF v_available_staff IS NOT NULL THEN
        -- Assign driver to order
        UPDATE Orders 
        SET staff_id = v_available_staff, delivery_status = 'In Progress'
        WHERE order_id = p_order_id;
        
        -- Mark driver as unavailable
        UPDATE Staff 
        SET is_available = FALSE, last_delivery_time = NOW()
        WHERE staff_id = v_available_staff;
        
        SET p_staff_id = v_available_staff;
        SET p_status = 'SUCCESS: Driver assigned';
    ELSE
        SET p_staff_id = 0;
        SET p_status = 'WARNING: No available drivers in area';
    END IF;
    
    COMMIT;
END //
DELIMITER ;
