DROP DATABASE IF EXISTS mamma_mia_pizza;
CREATE DATABASE mamma_mia_pizza;
USE mamma_mia_pizza;

-- 1. User table
CREATE TABLE `User` (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender ENUM('Male', 'Female', 'Other') DEFAULT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL CHECK (date_of_birth >= '1900-01-01' AND date_of_birth <= '2025-12-31'),
    address VARCHAR(255),
    postal_code VARCHAR(20),
    user_type ENUM('Customer','Staff','Admin') NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Email format check - simplified for MySQL compatibility
    CHECK (email LIKE '%@%.%' AND LENGTH(email) >= 5)
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
    discount_amount DECIMAL(6,2) DEFAULT 0.00 CHECK (discount_amount >= 0),
    final_total DECIMAL(8,2) CHECK (final_total >= 0),
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
    discount_value DECIMAL(5,2) CHECK (discount_value >= 0),
    is_used BOOLEAN DEFAULT FALSE,
    expiry_date DATE NOT NULL CHECK (expiry_date >= '2020-01-01')
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



-- Simple view for pizza menu with pricing (calculated in application)
CREATE VIEW pizza_menu AS
SELECT 
    p.pizza_id,
    p.name,
    p.description,
    GROUP_CONCAT(i.name SEPARATOR ', ') as ingredients_list
FROM pizzas p
JOIN pizza_ingredients pi ON p.pizza_id = pi.pizza_id
JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
GROUP BY p.pizza_id, p.name, p.description;

-- Simple view for order summary with customer info
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
    c.total_pizzas_ordered
FROM Orders o
JOIN Customer c ON o.customer_id = c.customer_id
JOIN `User` u ON c.user_id = u.user_id;

-- View for undelivered orders (required for reports)
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
