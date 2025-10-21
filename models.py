# stuff we need to import for database
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# make database connection
db = SQLAlchemy()

class User(db.Model):
    # all users go here - customers and staff
    __tablename__ = 'User'
    
    # basic info about each person
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.Enum('Male', 'Female', 'Other', name='gender_enum'))
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255))
    postal_code = db.Column(db.String(20))
    user_type = db.Column(db.Enum('Customer', 'Staff', 'Admin', name='user_type_enum'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.now)
    
    # connect to other tables
    customer = db.relationship('Customer', backref='user_info', uselist=False)
    staff = db.relationship('Staff', backref='user_info', uselist=False)
    
    def get_full_name(self):
        # just put first and last name together
        return f"{self.first_name} {self.last_name}"
    
    def is_birthday_today(self):
        # check if its their birthday today
        today = date.today()
        return (self.date_of_birth.month == today.month and 
                self.date_of_birth.day == today.day)
    
    def __repr__(self):
        return f'<User {self.get_full_name()}>'

class Customer(db.Model):
    # people who order pizzas
    __tablename__ = 'Customer'
    
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_pizzas_ordered = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    
    # link to their orders
    orders = db.relationship('Order', backref='customer_info', lazy=True)
    
    def is_loyal_customer(self):
        # loyal customers get discount if they ordered 10+ pizzas
        return self.total_pizzas_ordered >= 10
    
    def __repr__(self):
        return f'<Customer {self.customer_id}>'

class Staff(db.Model):
    # people who work here and deliver pizzas
    __tablename__ = 'Staff'
    
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    last_delivery_time = db.Column(db.DateTime)
    is_available = db.Column(db.Boolean, default=True)
    assigned_postal_code = db.Column(db.String(20))  # what area they deliver to
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    
    # orders they deliver
    orders = db.relationship('Order', backref='staff_info', lazy=True)
    
    def can_deliver_now(self):
        # check if driver can work (they need 30 min break)
        if self.last_delivery_time is None:
            return True
        time_since_delivery = datetime.now() - self.last_delivery_time
        return time_since_delivery.total_seconds() >= 1800  # 30 minutes
    
    def __repr__(self):
        return f'<Staff {self.staff_id}>'

class Ingredient(db.Model):
    # stuff we put on pizzas
    __tablename__ = 'ingredients'
    
    ingredient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    cost_per_unit = db.Column(db.Numeric(8, 2), nullable=False)
    category = db.Column(db.Enum('Meat', 'Dairy', 'Vegetable', 'Vegan', 'Other', name='ingredient_category_enum'), 
                        nullable=False, default='Vegetable')
    
    # connect to pizzas
    pizza_ingredients = db.relationship('PizzaIngredient', backref='ingredient_info', lazy=True)
    
    def is_vegetarian_friendly(self):
        # check if vegetarians can eat this
        return self.category in ['Vegetable', 'Dairy', 'Vegan', 'Other']
    
    def is_vegan_friendly(self):
        # check if vegans can eat this
        return self.category in ['Vegan', 'Vegetable', 'Other']
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class Pizza(db.Model):
    # pizzas we sell
    __tablename__ = 'pizzas'
    
    pizza_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    
    # connect to ingredients and orders
    pizza_ingredients = db.relationship('PizzaIngredient', backref='pizza_info', lazy=True)
    order_items = db.relationship('OrderItem', backref='pizza_info', lazy=True)
    
    @property
    def ingredients(self):
        # get all ingredients for this pizza
        return [pi.ingredient_info for pi in self.pizza_ingredients]
    
    def is_vegetarian(self):
        # check if vegetarians can eat this pizza
        for pizza_ingredient in self.pizza_ingredients:
            if not pizza_ingredient.ingredient_info.is_vegetarian_friendly():
                return False
        return True
    
    def is_vegan(self):
        # check if vegans can eat this pizza
        for pizza_ingredient in self.pizza_ingredients:
            if not pizza_ingredient.ingredient_info.is_vegan_friendly():
                return False
        return True
    
    def calculate_base_cost(self):
        # add up cost of all ingredients
        total_cost = 0
        for pizza_ingredient in self.pizza_ingredients:
            total_cost += float(pizza_ingredient.ingredient_info.cost_per_unit)
        return total_cost
    
    def calculate_final_price(self):
        # work out selling price with profit and tax
        base_cost = self.calculate_base_cost()
        with_profit = base_cost * 1.40  # add 40% profit
        with_tax = with_profit * 1.09   # add 9% tax
        return round(with_tax, 2)
    
    # easy way to get price
    @property
    def final_price(self):
        return self.calculate_final_price()
    
    def __repr__(self):
        return f'<Pizza {self.name}>'

class PizzaIngredient(db.Model):
    __tablename__ = 'pizza_ingredients'
    
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.pizza_id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.ingredient_id'), primary_key=True)
    
    def __repr__(self):
        return f'<PizzaIngredient P{self.pizza_id}-I{self.ingredient_id}>'

class Drink(db.Model):
    # drinks we sell
    __tablename__ = 'drinks'
    
    drink_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    
    # Links to orders
    order_items = db.relationship('OrderItem', backref='drink_info', lazy=True)
    
    def __repr__(self):
        return f'<Drink {self.name}>'

class Dessert(db.Model):
    # desserts we sell
    __tablename__ = 'desserts'
    
    dessert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    
    # Links to orders
    order_items = db.relationship('OrderItem', backref='dessert_info', lazy=True)
    
    def __repr__(self):
        return f'<Dessert {self.name}>'

class Order(db.Model):
    # customer orders
    __tablename__ = 'Orders'
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.customer_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('Staff.staff_id'))
    delivery_status = db.Column(db.Enum('Pending', 'In Progress', 'Out for Delivery', 'Delivered', 'Cancelled', 
                                       name='delivery_status_enum'), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    discount_amount = db.Column(db.Numeric(6, 2), default=0.00)
    final_total = db.Column(db.Numeric(8, 2))
    
    # Links to order items, discounts, and payments
    order_items = db.relationship('OrderItem', backref='order_info', lazy=True, cascade='all, delete-orphan')
    order_discounts = db.relationship('OrderDiscount', backref='order_info', lazy=True)
    transactions = db.relationship('Transaction', backref='order_info', lazy=True)
    
    def calculate_subtotal(self):
        # add up all item prices
        subtotal = 0
        for item in self.order_items:
            subtotal += float(item.total_price)
        return subtotal
    
    def calculate_total_with_discount(self):
        # work out final price after discounts
        subtotal = self.calculate_subtotal()
        total_discount = float(self.discount_amount) if self.discount_amount else 0
        return subtotal - total_discount
    
    def __repr__(self):
        return f'<Order {self.order_id}>'

class OrderItem(db.Model):
    # items in each order
    __tablename__ = 'Order_Item'
    
    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    item_type = db.Column(db.Enum('Pizza', 'Drink', 'Dessert', name='item_type_enum'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.pizza_id'))
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.drink_id'))
    dessert_id = db.Column(db.Integer, db.ForeignKey('desserts.dessert_id'))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(8, 2), nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'

class DiscountCode(db.Model):
    # discount codes for customers
    __tablename__ = 'Discount_Code'
    
    code_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_name = db.Column(db.String(50), unique=True, nullable=False)
    discount_value = db.Column(db.Numeric(5, 2))
    is_used = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.Date, nullable=False)
    
    # Links to orders where this code was used
    order_discounts = db.relationship('OrderDiscount', backref='discount_code_info', lazy=True)
    
    def is_still_valid(self):
        """Check if the discount code can still be used"""
        today = date.today()
        return not self.is_used and self.expiry_date >= today
    
    def __repr__(self):
        return f'<DiscountCode {self.code_name}>'

class OrderDiscount(db.Model):
    __tablename__ = 'Order_Discount'
    
    order_discount_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    code_id = db.Column(db.Integer, db.ForeignKey('Discount_Code.code_id'), nullable=False)
    discount_type = db.Column(db.Enum('Percentage', 'FixedAmount', 'FreePizza', 'FreeDrink', 
                                     name='discount_type_enum'), nullable=False)
    discount_amount = db.Column(db.Numeric(6, 2))
    
    def __repr__(self):
        return f'<OrderDiscount {self.order_discount_id}>'

class Transaction(db.Model):
    __tablename__ = 'Transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    transaction_amount = db.Column(db.Numeric(8, 2), nullable=False)
    transaction_status = db.Column(db.Enum('Pending', 'Paid', 'Failed', 'Refunded', 
                                          name='transaction_status_enum'), default='Pending')
    payment_method = db.Column(db.Enum('Cash', 'Card', 'Online', name='payment_method_enum'), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'