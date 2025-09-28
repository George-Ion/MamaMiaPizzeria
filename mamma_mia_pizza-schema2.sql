%%sql 
-- Drop database if exists and create a new one
DROP DATABASE IF EXISTS mamma_mia_pizza;
CREATE DATABASE mamma_mia_pizza;
USE mamma_mia_pizza;

-- Ingredients table
CREATE TABLE ingredients (
    ingredient_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cost_per_unit DECIMAL(8,2) DEFAULT 0
);

-- Pizzas table
CREATE TABLE pizzas (
    pizza_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    size VARCHAR(10) DEFAULT 'medium'
);

-- Pizza_ingredients table (many-to-many between pizzas and ingredients)
CREATE TABLE pizza_ingredients (
    pizza_id INT,
    ingredient_id INT,
    quantity DECIMAL(8,2) DEFAULT 0,
    PRIMARY KEY (pizza_id, ingredient_id),
    FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

-- Drinks table
CREATE TABLE drinks (
    drink_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(8,2) DEFAULT 0
);

-- Desserts table
CREATE TABLE desserts (
    dessert_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(8,2) DEFAULT 0
);

-- User table
CREATE TABLE User (
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

-- Customer table
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    total_pizzas_ordered INT DEFAULT 0,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Staff table
CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    position ENUM('Chef','Cashier','Driver','Manager') NOT NULL,
    hourly_rate DECIMAL(6,2),
    is_available BOOLEAN DEFAULT TRUE,
    is_delivery_person BOOLEAN DEFAULT FALSE,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Orders table
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

-- Order Item table (now with missing foreign keys added)
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

-- Discount Code table
CREATE TABLE Discount_Code (
    code_id INT AUTO_INCREMENT PRIMARY KEY,
    code_name VARCHAR(50) UNIQUE NOT NULL,
    discount_value DECIMAL(5,2),
    is_used BOOLEAN DEFAULT FALSE,
    expiry_date DATE NOT NULL
);

-- Order Discount table
CREATE TABLE Order_Discount (
    order_discount_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    code_id INT NOT NULL,
    discount_type ENUM('Percentage','FixedAmount','FreePizza','FreeDrink') NOT NULL,
    discount_amount DECIMAL(6,2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (code_id) REFERENCES Discount_Code(code_id)
);

-- Transaction table
CREATE TABLE Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    transaction_amount DECIMAL(8,2) NOT NULL,
    transaction_status ENUM('Pending','Paid','Failed','Refunded') DEFAULT 'Pending',
    payment_method ENUM('Cash','Card','Online') NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
);