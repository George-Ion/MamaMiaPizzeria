from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Customer, Staff, Pizza, Drink, Dessert, Order, OrderItem, DiscountCode
from datetime import datetime, timedelta

# Create blueprints
users_bp = Blueprint('users', __name__)
orders_bp = Blueprint('orders', __name__)
products_bp = Blueprint('products', __name__)

# Users routes
@users_bp.route('/users')
def show_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@users_bp.route('/users/<int:user_id>')
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user)

@users_bp.route('/customers')
def show_customers():
    customers = db.session.query(Customer, User).join(User).all()
    return render_template('customers.html', customers=customers)

# Products routes
@products_bp.route('/products')
def show_menu():
    pizzas = Pizza.query.all()
    drinks = Drink.query.all() 
    desserts = Dessert.query.all()
    return render_template('menu.html', pizzas=pizzas, drinks=drinks, desserts=desserts)

@products_bp.route('/pizzas')
def show_pizzas():
    pizzas = Pizza.query.all()
    return render_template('pizzas.html', pizzas=pizzas)

# Orders routes
@orders_bp.route('/orders')
def show_orders():
    orders = db.session.query(Order, Customer, User).join(Customer).join(User).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@orders_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    user = User.query.get(customer.user_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('order_detail.html', order=order, customer=customer, user=user, items=items)

@orders_bp.route('/orders/new')
def new_order():
    customers = db.session.query(Customer, User).join(User).all()
    pizzas = Pizza.query.all()
    drinks = Drink.query.all()
    desserts = Dessert.query.all()
    return render_template('new_order.html', customers=customers, pizzas=pizzas, drinks=drinks, desserts=desserts)

@orders_bp.route('/orders/create', methods=['POST'])
def create_order():
    customer_id = request.form.get('customer_id')
    
    # Create the order
    order = Order()
    order.customer_id = customer_id
    order.delivery_status = 'Pending'
    order.discount_amount = 0.00
    
    db.session.add(order)
    db.session.flush()  # Get the ID
    
    total = 0.00
    pizza_count = 0
    
    # Add pizzas to order
    for pizza in Pizza.query.all():
        qty = request.form.get(f'pizza_{pizza.pizza_id}')
        if qty and int(qty) > 0:
            qty = int(qty)
            pizza_count += qty
            item_total = float(pizza.final_price) * qty  # Convert Decimal to float for calculation
            total += item_total
            
            item = OrderItem()
            item.order_id = order.order_id
            item.item_type = 'Pizza'
            item.pizza_id = pizza.pizza_id
            item.quantity = qty
            item.total_price = item_total
            db.session.add(item)
    
    # Add drinks 
    for drink in Drink.query.all():
        qty = request.form.get(f'drink_{drink.drink_id}')
        if qty and int(qty) > 0:
            item_total = float(drink.price) * int(qty)
            total += item_total
            
            item = OrderItem()
            item.order_id = order.order_id
            item.item_type = 'Drink'
            item.drink_id = drink.drink_id
            item.quantity = int(qty)
            item.total_price = item_total
            db.session.add(item)
    
    # Add desserts
    for dessert in Dessert.query.all():
        qty = request.form.get(f'dessert_{dessert.dessert_id}')
        if qty and int(qty) > 0:
            item_total = float(dessert.price) * int(qty)
            total += item_total
            
            item = OrderItem()
            item.order_id = order.order_id
            item.item_type = 'Dessert'
            item.dessert_id = dessert.dessert_id
            item.quantity = int(qty)
            item.total_price = item_total
            db.session.add(item)
    
    # Check if customer gets loyalty discount
    customer = Customer.query.get(customer_id)
    discount = 0.00
    
    if customer.total_pizzas_ordered >= 10:
        discount = total * 0.10
        order.discount_amount = discount
    
    # Check discount code
    discount_code = request.form.get('discount_code')
    if discount_code:
        code = DiscountCode.query.filter_by(code_name=discount_code, is_used=False).first()
        if code:
            discount += float(code.discount_value)
            order.discount_amount = discount
            code.is_used = True
    
    order.final_total = total - discount
    customer.total_pizzas_ordered += pizza_count
    
    db.session.commit()
    flash(f'Order #{order.order_id} created successfully!')
    return redirect(url_for('orders.order_detail', order_id=order.order_id))

@orders_bp.route('/reports')
def show_reports():
    # Get top pizzas from last month
    last_month = datetime.now() - timedelta(days=30)
    
    top_pizzas = db.session.query(
        Pizza.name,
        db.func.sum(OrderItem.quantity).label('sold')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= last_month
    ).group_by(Pizza.pizza_id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(3).all()
    
    # Get customer stats
    total_customers = Customer.query.count()
    loyalty_customers = Customer.query.filter(Customer.total_pizzas_ordered >= 10).count()
    
    # Revenue this month
    monthly_revenue = db.session.query(db.func.sum(Order.final_total)).filter(
        Order.created_at >= last_month
    ).scalar() or 0
    
    return render_template('reports.html', 
                         top_pizzas=top_pizzas,
                         total_customers=total_customers,
                         loyalty_customers=loyalty_customers,
                         monthly_revenue=monthly_revenue)