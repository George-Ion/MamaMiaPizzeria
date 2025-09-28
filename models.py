from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import CheckConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255))
    postal_code = db.Column(db.String(20))
    user_type = db.Column(db.Enum('Customer', 'Staff', 'Admin', name='user_type_enum'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='user_info', uselist=False)
    staff = db.relationship('Staff', backref='user_info', uselist=False)
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.full_name}>'

class Customer(db.Model):
    __tablename__ = 'Customer'
    
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_pizzas_ordered = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    
    # Relationships
    orders = db.relationship('Order', backref='customer_info', lazy=True)
    
    @hybrid_property
    def is_loyalty_eligible(self):
        return self.total_pizzas_ordered >= 10
    
    def __repr__(self):
        return f'<Customer {self.customer_id}>'

class Staff(db.Model):
    __tablename__ = 'Staff'
    
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    last_delivery_time = db.Column(db.DateTime)
    is_available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    
    # Relationships
    orders = db.relationship('Order', backref='staff_info', lazy=True)
    
    def __repr__(self):
        return f'<Staff {self.staff_id}>'

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    
    ingredient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    cost_per_unit = db.Column(db.Numeric(8, 2), nullable=False)
    category = db.Column(db.Enum('Meat', 'Dairy', 'Vegetable', 'Vegan', 'Other', name='ingredient_category_enum'), 
                        nullable=False, default='Vegetable')
    
    # Generated columns (computed in Python since MySQL generated columns aren't well supported in SQLAlchemy)
    @hybrid_property
    def is_vegetarian(self):
        return self.category in ['Vegetable', 'Dairy', 'Vegan', 'Other']
    
    @hybrid_property
    def is_vegan(self):
        return self.category in ['Vegan', 'Vegetable', 'Other']
    
    # Relationships
    pizza_ingredients = db.relationship('PizzaIngredient', backref='ingredient_info', lazy=True)
    
    __table_args__ = (
        CheckConstraint('cost_per_unit > 0'),
    )
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class Pizza(db.Model):
    __tablename__ = 'pizzas'
    
    pizza_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    pizza_ingredients = db.relationship('PizzaIngredient', backref='pizza_info', lazy=True)
    order_items = db.relationship('OrderItem', backref='pizza_info', lazy=True)
    
    @hybrid_property
    def is_vegetarian(self):
        for pi in self.pizza_ingredients:
            if not pi.ingredient_info.is_vegetarian:
                return False
        return True
    
    @hybrid_property
    def is_vegan(self):
        for pi in self.pizza_ingredients:
            if not pi.ingredient_info.is_vegan:
                return False
        return True
    
    @hybrid_property
    def base_cost(self):
        total_cost = 0
        for pi in self.pizza_ingredients:
            total_cost += float(pi.ingredient_info.cost_per_unit)  # Each ingredient has quantity 1
        return total_cost
    
    @hybrid_property
    def final_price(self):
        # Base cost + 40% margin + 9% VAT
        base_cost = self.base_cost
        with_margin = base_cost * 1.40
        with_vat = with_margin * 1.09
        return round(with_vat, 2)
    
    def __repr__(self):
        return f'<Pizza {self.name}>'

class PizzaIngredient(db.Model):
    __tablename__ = 'pizza_ingredients'
    
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.pizza_id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.ingredient_id'), primary_key=True)
    
    def __repr__(self):
        return f'<PizzaIngredient P{self.pizza_id}-I{self.ingredient_id}>'

class Drink(db.Model):
    __tablename__ = 'drinks'
    
    drink_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='drink_info', lazy=True)
    
    __table_args__ = (
        CheckConstraint('price > 0'),
    )
    
    def __repr__(self):
        return f'<Drink {self.name}>'

class Dessert(db.Model):
    __tablename__ = 'desserts'
    
    dessert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='dessert_info', lazy=True)
    
    __table_args__ = (
        CheckConstraint('price > 0'),
    )
    
    def __repr__(self):
        return f'<Dessert {self.name}>'

class Order(db.Model):
    __tablename__ = 'Orders'
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.customer_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('Staff.staff_id'))
    delivery_status = db.Column(db.Enum('Pending', 'In Progress', 'Out for Delivery', 'Delivered', 'Cancelled', 
                                       name='delivery_status_enum'), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    discount_amount = db.Column(db.Numeric(6, 2), default=0.00)
    final_total = db.Column(db.Numeric(8, 2))
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order_info', lazy=True, cascade='all, delete-orphan')
    order_discounts = db.relationship('OrderDiscount', backref='order_info', lazy=True)
    transactions = db.relationship('Transaction', backref='order_info', lazy=True)
    
    @hybrid_property
    def subtotal(self):
        return sum(item.total_price for item in self.order_items)
    
    def calculate_total(self):
        subtotal = float(self.subtotal or 0)
        discount = float(self.discount_amount or 0)
        return round(subtotal - discount, 2)
    
    def __repr__(self):
        return f'<Order {self.order_id}>'

class OrderItem(db.Model):
    __tablename__ = 'Order_Item'
    
    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'), nullable=False)
    item_type = db.Column(db.Enum('Pizza', 'Drink', 'Dessert', name='item_type_enum'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.pizza_id'))
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.drink_id'))
    dessert_id = db.Column(db.Integer, db.ForeignKey('desserts.dessert_id'))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(8, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint('quantity > 0'),
    )
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'

class DiscountCode(db.Model):
    __tablename__ = 'Discount_Code'
    
    code_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_name = db.Column(db.String(50), unique=True, nullable=False)
    discount_value = db.Column(db.Numeric(5, 2))
    is_used = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.Date, nullable=False)
    
    # Relationships
    order_discounts = db.relationship('OrderDiscount', backref='discount_code_info', lazy=True)
    
    @hybrid_property
    def is_valid(self):
        from datetime import date
        return not self.is_used and self.expiry_date >= date.today()
    
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
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'