# Import what we need for our pizza website
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Customer, Staff, Pizza, Drink, Dessert, Order, OrderItem, DiscountCode, OrderDiscount
from datetime import datetime, timedelta, date

# Create different sections of our website
users_bp = Blueprint('users', __name__)      # For managing users
orders_bp = Blueprint('orders', __name__)    # For managing orders
products_bp = Blueprint('products', __name__)  # For showing menu

# === USER PAGES ===
@users_bp.route('/users')
def show_users():
    """Show a list of all users"""
    users = User.query.all()
    return render_template('users.html', users=users)

@users_bp.route('/users/<int:user_id>')
def user_detail(user_id):
    """Show details about one specific user"""
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user)

# === MENU/PRODUCTS PAGES ===
@products_bp.route('/products')
def show_menu():
    """Show our pizza menu where customers can place orders"""
    # Get all the food we sell
    pizzas = Pizza.query.all()
    drinks = Drink.query.all() 
    desserts = Dessert.query.all()
    
    # Get list of customers so they can place orders
    customers = db.session.query(Customer, User).join(User).all()
    
    return render_template('menu.html', 
                         pizzas=pizzas, 
                         drinks=drinks, 
                         desserts=desserts, 
                         customers=customers)

@products_bp.route('/pizzas')
def show_pizzas():
    """Show just the pizzas"""
    pizzas = Pizza.query.all()
    return render_template('pizzas.html', pizzas=pizzas)

# === ORDER PAGES ===
@orders_bp.route('/orders')
def show_orders():
    """Show all orders with customer names"""
    # Get orders with customer information
    orders = db.session.query(Order, Customer, User)\
        .join(Customer, Order.customer_id == Customer.customer_id)\
        .join(User, Customer.user_id == User.user_id)\
        .order_by(Order.created_at.desc()).all()
    
    return render_template('orders.html', orders=orders)

@orders_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Show details about one specific order"""
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Get customer information
    customer = Customer.query.get(order.customer_id)
    user = User.query.get(customer.user_id)
    
    # Get all items in this order
    items = OrderItem.query.filter_by(order_id=order_id).all()
    
    return render_template('order_detail.html', 
                         order=order, 
                         customer=customer, 
                         user=user, 
                         items=items)

@orders_bp.route('/orders/create', methods=['POST'])
def create_order():
    """Create a new pizza order - SIMPLIFIED VERSION"""
    
    # Get who is ordering
    customer_id = request.form.get('customer_id')
    discount_code = request.form.get('discount_code', '').strip()
    
    if not customer_id:
        flash('Please select a customer!', 'error')
        return redirect(url_for('products.show_menu'))
    
    # Start database transaction explicitly
    try:
        db.session.begin()
        
        # Step 1: Get customer information
        customer = Customer.query.get(customer_id)
        user = User.query.get(customer.user_id if customer else None)
        
        # Step 2: Create a new order
        new_order = Order()
        new_order.customer_id = customer_id
        new_order.delivery_status = 'Pending'
        new_order.discount_amount = 0.00
        
        db.session.add(new_order)
        db.session.flush()  # Save to get order ID
        
        # Step 3: Add items to the order
        total_price = 0.00
        pizza_count = 0
        has_items = False
        
        # Add pizzas with validation
        for pizza in Pizza.query.all():
            quantity = request.form.get(f'pizza_{pizza.pizza_id}')
            if quantity and int(quantity) > 0:
                quantity = int(quantity)
                pizza_count += quantity
                has_items = True
                
                # Calculate price for this pizza type
                price_per_pizza = float(pizza.final_price)
                item_total = price_per_pizza * quantity
                total_price += item_total
                
                # Create order item
                order_item = OrderItem()
                order_item.order_id = new_order.order_id
                order_item.item_type = 'Pizza'
                order_item.pizza_id = pizza.pizza_id
                order_item.quantity = quantity
                order_item.total_price = item_total
                db.session.add(order_item)
        
        # Add drinks
        for drink in Drink.query.all():
            quantity = request.form.get(f'drink_{drink.drink_id}')
            if quantity and int(quantity) > 0:
                quantity = int(quantity)
                has_items = True
                
                # Calculate price for this drink type
                item_total = float(drink.price) * quantity
                total_price += item_total
                
                # Create order item
                order_item = OrderItem()
                order_item.order_id = new_order.order_id
                order_item.item_type = 'Drink'
                order_item.drink_id = drink.drink_id
                order_item.quantity = quantity
                order_item.total_price = item_total
                db.session.add(order_item)
        
        # Add desserts
        for dessert in Dessert.query.all():
            quantity = request.form.get(f'dessert_{dessert.dessert_id}')
            if quantity and int(quantity) > 0:
                quantity = int(quantity)
                has_items = True
                
                # Calculate price for this dessert type
                item_total = float(dessert.price) * quantity
                total_price += item_total
                
                # Create order item
                order_item = OrderItem()
                order_item.order_id = new_order.order_id
                order_item.item_type = 'Dessert'
                order_item.dessert_id = dessert.dessert_id
                order_item.quantity = quantity
                order_item.total_price = item_total
                db.session.add(order_item)
        
        # Check if any items were added
        if not has_items:
            flash('Please add at least one item to your order!', 'error')
            return redirect(url_for('products.show_menu'))
        
        # Step 4: Calculate discounts
        total_discount = 0.00
        discount_messages = []
        
        # A) Loyalty discount (10% off for customers with 10+ pizzas, then reset counter)
        loyalty_discount_applied = False
        if customer.is_loyal_customer():
            loyalty_discount = total_price * 0.10
            total_discount += loyalty_discount
            discount_messages.append(f'Loyalty discount: €{loyalty_discount:.2f} (10% off for {customer.total_pizzas_ordered} pizzas ordered!)')
            loyalty_discount_applied = True
        
        # B) Birthday discount (free cheapest pizza + free drink if ordered)
        if user.is_birthday_today():
            birthday_discount = 0.00
            birthday_items = []
            
            # Find cheapest pizza in order and give it for free
            pizza_items = OrderItem.query.filter_by(order_id=new_order.order_id, item_type='Pizza').all()
            if pizza_items:
                cheapest_pizza_price = min(float(item.total_price) / item.quantity for item in pizza_items)
                birthday_discount += cheapest_pizza_price
                birthday_items.append(f'Free cheapest pizza: €{cheapest_pizza_price:.2f}')
            
            # Give one free drink if drinks are ordered
            drink_items = OrderItem.query.filter_by(order_id=new_order.order_id, item_type='Drink').all()
            if drink_items:
                # Find cheapest drink and give one for free
                cheapest_drink_price = min(float(item.total_price) / item.quantity for item in drink_items)
                birthday_discount += cheapest_drink_price
                birthday_items.append(f'Free drink: €{cheapest_drink_price:.2f}')
            
            if birthday_items:
                discount_messages.append(f'Happy Birthday {user.first_name}! {", ".join(birthday_items)}')
            else:
                discount_messages.append(f'Happy Birthday {user.first_name}! Order a pizza to get your birthday discount!')
            
            total_discount += birthday_discount
        
        # C) Discount code
        if discount_code:
            code = DiscountCode.query.filter_by(code_name=discount_code).first()
            if code and code.is_still_valid():
                code_discount = float(code.discount_value)
                total_discount += code_discount
                discount_messages.append(f'Discount code "{discount_code}": €{code_discount:.2f} off')
                
                # Mark code as used
                code.is_used = True
                db.session.add(code)
            else:
                discount_messages.append(f'Invalid or expired discount code: {discount_code}')
        
        # Step 5: Assign delivery driver
        try:
            # Find a driver for this postal code area
            driver = Staff.query.join(User).filter(
                Staff.assigned_postal_code == user.postal_code,
                Staff.is_available == True
            ).first()
            
            if driver and driver.can_deliver_now():
                new_order.staff_id = driver.staff_id
                new_order.delivery_status = 'In Progress'
                driver.is_available = False
                driver.last_delivery_time = datetime.utcnow()
                
                driver_user = User.query.get(driver.user_id)
                discount_messages.append(f'Driver assigned: {driver_user.get_full_name()}')
            else:
                discount_messages.append(f'No drivers available for area {user.postal_code}')
        except Exception as e:
            discount_messages.append(f'Driver assignment pending')
        
        # Step 6: Finalize the order
        # Make sure discount doesn't exceed total
        if total_discount > total_price:
            total_discount = total_price
        
        final_total = total_price - total_discount
        new_order.discount_amount = total_discount
        new_order.final_total = final_total
        customer.total_pizzas_ordered += pizza_count
        
        # Reset loyalty counter if loyalty discount was applied
        if loyalty_discount_applied:
            customer.total_pizzas_ordered = 0
        
        # Final validation before commit
        if customer.total_pizzas_ordered < 0:
            raise ValueError("Invalid customer pizza count after update")
        
        # Save everything in transaction
        db.session.add(new_order)
        db.session.add(customer)
        db.session.commit()
        
        # Step 7: Show success message
        success_message = f'Order #{new_order.order_id} created! Total: €{new_order.final_total:.2f}'
        if total_discount > 0:
            success_message += f' (Saved: €{total_discount:.2f})'
        
        flash(success_message, 'success')
        for message in discount_messages:
            flash(message, 'info')
        
        return redirect(url_for('orders.order_detail', order_id=new_order.order_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Order failed - all changes rolled back: {str(e)}', 'error')
        return redirect(url_for('products.show_menu'))

@orders_bp.route('/reports')
def show_reports():
    """Show simple business reports"""
    # Get most popular pizzas from last month
    last_month = datetime.now() - timedelta(days=30)
    
    popular_pizzas = db.session.query(
        Pizza.name,
        db.func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= last_month
    ).group_by(Pizza.pizza_id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(3).all()
    
    # Count customers
    total_customers = Customer.query.count()
    loyal_customers = Customer.query.filter(Customer.total_pizzas_ordered >= 10).count()
    
    # Calculate monthly revenue
    monthly_revenue = db.session.query(db.func.sum(Order.final_total)).filter(
        Order.created_at >= last_month
    ).scalar() or 0
    
    return render_template('reports.html', 
                         top_pizzas=popular_pizzas,
                         total_customers=total_customers,
                         loyalty_customers=loyal_customers,
                         monthly_revenue=monthly_revenue)

@orders_bp.route('/orders/<int:order_id>/complete_delivery', methods=['POST'])
def complete_delivery(order_id):
    """Mark an order as delivered"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.staff_id:
            # Mark order as delivered
            order.delivery_status = 'Delivered'
            
            # Make driver available again (but with 30 minute cooldown)
            driver = Staff.query.get(order.staff_id)
            driver.last_delivery_time = datetime.utcnow()
            driver.is_available = True
            
            db.session.commit()
            
            driver_user = User.query.get(driver.user_id)
            flash(f'Delivery completed by {driver_user.get_full_name()}!', 'success')
        else:
            flash('No driver assigned to this order', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing delivery: {str(e)}', 'error')
    
    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/delivery-status')
def delivery_status():
    """Show which drivers are available"""
    try:
        # Get all delivery staff with their information
        staff_list = []
        all_staff = Staff.query.join(User).all()
        
        for staff in all_staff:
            user = User.query.get(staff.user_id)
            
            # Check availability status
            if staff.can_deliver_now():
                status = 'Available'
            else:
                minutes_left = 30 - int((datetime.utcnow() - staff.last_delivery_time).total_seconds() / 60)
                status = f'Unavailable for {minutes_left} more minutes'
            
            staff_info = {
                'staff_id': staff.staff_id,
                'staff_name': user.get_full_name(),
                'phone': user.phone,
                'assigned_postal_code': staff.assigned_postal_code,
                'is_available': staff.is_available,
                'last_delivery_time': staff.last_delivery_time,
                'availability_status': status
            }
            staff_list.append(staff_info)
        
        return render_template('delivery_status.html', staff_list=staff_list)
        
    except Exception as e:
        flash(f'Error loading delivery status: {str(e)}', 'error')
        return redirect(url_for('orders.show_orders'))

@orders_bp.route('/admin/reset-discount-codes', methods=['POST'])
def reset_discount_codes():
    """Reset all discount codes so they can be used again (for testing)"""
    try:
        # Get all discount codes and make them valid again
        codes = DiscountCode.query.all()
        count = 0
        
        for code in codes:
            code.is_used = False
            code.expiry_date = date(2026, 12, 31)  # Set expiry to end of 2026
            count += 1
        
        db.session.commit()
        flash(f'Reset {count} discount codes - they can all be used again!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting discount codes: {str(e)}', 'error')
    
    return redirect(url_for('orders.show_reports'))