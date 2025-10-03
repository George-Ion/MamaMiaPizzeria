from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Customer, Staff, Pizza, Drink, Dessert, Order, OrderItem, DiscountCode, OrderDiscount
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

# Products routes
@products_bp.route('/products')
def show_menu():
    # Get all menu items
    pizzas = Pizza.query.all()
    drinks = Drink.query.all() 
    desserts = Dessert.query.all()
    
    # Get customers for order placement
    customers = db.session.query(Customer, User).join(User).all()
    
    return render_template('menu.html', pizzas=pizzas, drinks=drinks, desserts=desserts, customers=customers)

@products_bp.route('/pizzas')
def show_pizzas():
    pizzas = Pizza.query.all()
    return render_template('pizzas.html', pizzas=pizzas)

# Orders routes
@orders_bp.route('/orders')
def show_orders():
    """Display all orders with customer information"""
    # Fix the join by being explicit about the relationships
    orders = db.session.query(Order, Customer, User)\
        .join(Customer, Order.customer_id == Customer.customer_id)\
        .join(User, Customer.user_id == User.user_id)\
        .order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@orders_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    user = User.query.get(customer.user_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('order_detail.html', order=order, customer=customer, user=user, items=items)

@orders_bp.route('/orders/create', methods=['POST'])
def create_order():
    """Create a new order with complete business logic implementation"""
    customer_id = request.form.get('customer_id')
    discount_code = request.form.get('discount_code', '').strip()
    
    if not customer_id:
        flash('Please select a customer!', 'error')
        return redirect(url_for('products.show_menu'))
    
    try:
        # Get customer and user info for business logic
        customer = Customer.query.get(customer_id)
        user = User.query.get(customer.user_id)
        
        # Create the order
        order = Order()
        order.customer_id = customer_id
        order.delivery_status = 'Pending'
        order.discount_amount = 0.00
        
        db.session.add(order)
        db.session.flush()  # Get the ID
        
        total = 0.00
        pizza_count = 0
        order_has_items = False
        
        # Add pizzas to order
        for pizza in Pizza.query.all():
            qty = request.form.get(f'pizza_{pizza.pizza_id}')
            if qty and int(qty) > 0:
                qty = int(qty)
                pizza_count += qty
                order_has_items = True
                item_total = float(pizza.final_price) * qty
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
                order_has_items = True
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
                order_has_items = True
                item_total = float(dessert.price) * int(qty)
                total += item_total
                
                item = OrderItem()
                item.order_id = order.order_id
                item.item_type = 'Dessert'
                item.dessert_id = dessert.dessert_id
                item.quantity = int(qty)
                item.total_price = item_total
                db.session.add(item)
        
        # Check if order has any items
        if not order_has_items:
            db.session.rollback()
            flash('Please add at least one item to your order!', 'error')
            return redirect(url_for('products.show_menu'))
        
        # BUSINESS LOGIC IMPLEMENTATION
        discount_messages = []
        total_discount = 0.00
        
        # 1. 10-PIZZA LOYALTY DISCOUNT (10% off)
        if customer.total_pizzas_ordered >= 10:
            loyalty_discount = total * 0.10
            total_discount += loyalty_discount
            discount_messages.append(f'Loyalty Discount: €{loyalty_discount:.2f} (10% off for {customer.total_pizzas_ordered} pizzas ordered!)')
        
        # 2. BIRTHDAY FREEBIES
        from datetime import date
        today = date.today()
        if (user.date_of_birth.month == today.month and user.date_of_birth.day == today.day):
            # Find cheapest pizza and drink for birthday freebies
            cheapest_pizza = min([item for item in order.order_items if item.item_type == 'Pizza'], 
                                key=lambda x: x.total_price / x.quantity, default=None)
            cheapest_drink = min([item for item in order.order_items if item.item_type == 'Drink'], 
                               key=lambda x: x.total_price / x.quantity, default=None)
            
            birthday_discount = 0.00
            if cheapest_pizza:
                pizza_unit_price = cheapest_pizza.total_price / cheapest_pizza.quantity
                birthday_discount += pizza_unit_price
            if cheapest_drink:
                drink_unit_price = cheapest_drink.total_price / cheapest_drink.quantity
                birthday_discount += drink_unit_price
            
            total_discount += birthday_discount
            discount_messages.append(f'Happy Birthday {user.first_name}! Free pizza & drink: €{birthday_discount:.2f}')
        
        # 3. ONE-TIME DISCOUNT CODES
        if discount_code:
            code = DiscountCode.query.filter_by(code_name=discount_code, is_used=False).first()
            if code and code.is_valid:
                code_discount = min(float(code.discount_value), total - total_discount)  # Don't exceed order total
                total_discount += code_discount
                code.is_used = True
                discount_messages.append(f'Discount Code "{discount_code}": €{code_discount:.2f} off')
                
                # Record the discount usage
                from models import OrderDiscount
                order_discount = OrderDiscount()
                order_discount.order_id = order.order_id
                order_discount.code_id = code.code_id
                order_discount.discount_type = 'FixedAmount'
                order_discount.discount_amount = code_discount
                db.session.add(order_discount)
            else:
                discount_messages.append(f'Invalid or expired discount code: "{discount_code}"')
        
        # Apply discounts and finalize order
        order.discount_amount = total_discount
        order.final_total = total - total_discount
        customer.total_pizzas_ordered += pizza_count
        
        # 4. ASSIGN DELIVERY PERSON BASED ON POSTAL CODE
        delivery_assigned = False
        try:
            # Use SQL stored procedure to assign delivery driver
            result = db.session.execute(
                db.text("CALL assign_delivery_driver(:order_id, :postal_code, @staff_id, @status)"),
                {"order_id": order.order_id, "postal_code": user.postal_code}
            )
            
            # Get the results
            assignment_result = db.session.execute(db.text("SELECT @staff_id, @status")).fetchone()
            if assignment_result and assignment_result[0] and assignment_result[0] > 0:
                staff_id = assignment_result[0]
                status = assignment_result[1]
                
                # Get staff name for confirmation
                staff = Staff.query.get(staff_id)
                staff_user = User.query.get(staff.user_id)
                delivery_assigned = True
                discount_messages.append(f'Driver Assigned: {staff_user.first_name} {staff_user.last_name} (Area: {staff.assigned_postal_code})')
            else:
                discount_messages.append(f'No available drivers for area {user.postal_code}. Order will be assigned manually.')
        except Exception as e:
            print(f"Delivery assignment error: {e}")
            discount_messages.append(f'Driver assignment pending for area {user.postal_code}')
        
        db.session.commit()
        
        # Show success message with all applied discounts
        success_msg = f'Order #{order.order_id} created successfully! Total: €{order.final_total:.2f}'
        if total_discount > 0:
            success_msg += f' (Original: €{total:.2f}, Saved: €{total_discount:.2f})'
        
        flash(success_msg, 'success')
        for msg in discount_messages:
            flash(msg, 'info')
        
        return redirect(url_for('orders.order_detail', order_id=order.order_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating order: {str(e)}', 'error')
        return redirect(url_for('products.show_menu'))

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

@orders_bp.route('/orders/<int:order_id>/complete_delivery', methods=['POST'])
def complete_delivery(order_id):
    """Complete a delivery and implement 30-minute cooldown for driver"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.staff_id:
            # Mark order as delivered
            order.delivery_status = 'Delivered'
            
            # Mark driver as available again after cooldown logic
            staff = Staff.query.get(order.staff_id)
            staff.last_delivery_time = datetime.utcnow()
            staff.is_available = True  # They can take new deliveries after 30 min cooldown
            
            db.session.commit()
            
            user = User.query.get(staff.user_id)
            flash(f'Delivery completed! {user.first_name} {user.last_name} will be available for new deliveries in 30 minutes.', 'success')
        else:
            flash('No driver assigned to this order', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing delivery: {str(e)}', 'error')
    
    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/delivery-status')
def delivery_status():
    """Show delivery staff status and availability"""
    try:
        # Use the delivery_staff_view we created
        staff_status = db.session.execute(db.text("SELECT * FROM delivery_staff_view")).fetchall()
        staff_list = [dict(zip(['staff_id', 'staff_name', 'phone', 'assigned_postal_code', 
                              'is_available', 'last_delivery_time', 'availability_status'], row)) 
                     for row in staff_status]
        
        return render_template('delivery_status.html', staff_list=staff_list)
    except Exception as e:
        flash(f'Error loading delivery status: {str(e)}', 'error')
        return redirect(url_for('orders.show_orders'))

@orders_bp.route('/admin/reset-discount-codes', methods=['POST'])
def reset_discount_codes():
    """Admin function to reset all discount codes to valid state"""
    try:
        from datetime import date
        
        # Update all discount codes to be valid (not used, future expiry dates)
        updates = [
            ('WELCOME10', '2026-12-31'),
            ('PIZZA20', '2026-06-30'),
            ('SUMMER15', '2026-08-31'),
            ('STUDENT5', '2026-12-31'),
            ('FAMIGLIA25', '2026-07-31'),
            ('WEEKEND12', '2026-03-31'),
            ('LOYALTY30', '2026-09-30'),
            ('HAPPY18', '2026-05-31'),
            ('MAMMA50', '2026-04-30'),
            ('AMICI8', '2026-02-28')
        ]
        
        updated_count = 0
        for code_name, new_expiry in updates:
            code = DiscountCode.query.filter_by(code_name=code_name).first()
            if code:
                code.expiry_date = date.fromisoformat(new_expiry)
                code.is_used = False  # Reset all codes to unused
                updated_count += 1
        
        db.session.commit()
        flash(f'Successfully reset {updated_count} discount codes to valid state!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting discount codes: {str(e)}', 'error')
    
    return redirect(url_for('orders.show_reports'))