# my pizza website code
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, Customer, Staff, Pizza, Drink, Dessert, Order, OrderItem, DiscountCode, OrderDiscount, Ingredient
from datetime import datetime, timedelta, date
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, func, case
import random

def create_emergency_driver(postal_code):
    # make new driver when we need one
    try:
        # list of driver names we can use
        driver_names = [
            ('Express', 'Mario'), ('Veloce', 'Luigi'), ('Rapido', 'Giuseppe'),
            ('Sprint', 'Antonio'), ('Flash', 'Marco'), ('Turbo', 'Luca'),
            ('Speed', 'Andrea'), ('Fast', 'Matteo'), ('Quick', 'Franco'),
            ('Zoom', 'Roberto'), ('Rush', 'Paolo'), ('Jet', 'Simone')
        ]
        
        # pick random name
        surname, first_name = random.choice(driver_names)
        
        # make unique email with timestamp
        timestamp = str(int(datetime.now().timestamp()))[-6:]  # last 6 digits
        email = f'{first_name.lower()}.{surname.lower()}.{timestamp}@mammamiapizza.com'
        
        # make new user for the driver
        new_user = User(
            first_name=first_name,
            last_name=surname,
            gender='Male',  # just use male 
            email=email,
            phone=f'+39 380 {random.randint(1000000, 9999999)}',
            date_of_birth=date(1990, 1, 1),  # fake birthday
            address=f'Emergency Driver Address, Milano',
            postal_code=postal_code,  # same area as order
            user_type='Staff'
        )
        
        db.session.add(new_user)
        db.session.flush()  # get user id
        
        # make new staff record
        new_staff = Staff(
            user_id=new_user.user_id,
            assigned_postal_code=postal_code,
            is_available=True,
            last_delivery_time=None
        )
        
        db.session.add(new_staff)
        db.session.flush()  # get staff id
        return new_staff
        
    except Exception as e:
        return None

def update_delivery_statuses():
    # update order status automatically
    try:
        current_time = datetime.now()
        
        # change "In Progress" to "Out for Delivery" after 30 seconds
        in_progress_orders = Order.query.filter_by(delivery_status='In Progress').all()
        for order in in_progress_orders:
            if order.created_at and (current_time - order.created_at).total_seconds() >= 30:  # 30 seconds
                order.delivery_status = 'Out for Delivery'
                db.session.add(order)
        
        # change "Out for Delivery" to "Delivered" after 2 minutes
        # and let driver work again
        out_for_delivery_orders = Order.query.filter_by(delivery_status='Out for Delivery').all()
        for order in out_for_delivery_orders:
            if order.created_at and (current_time - order.created_at).total_seconds() >= 120:  # 2 minutes
                order.delivery_status = 'Delivered'
                db.session.add(order)
                
                # make driver available again
                if order.staff_id:
                    staff = Staff.query.get(order.staff_id)
                    if staff:
                        staff.is_available = True
                        staff.last_delivery_time = current_time
                        db.session.add(staff)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating delivery statuses: {e}")

# different parts of website
users_bp = Blueprint('users', __name__)      # user stuff
orders_bp = Blueprint('orders', __name__)    # order stuff
products_bp = Blueprint('products', __name__)  # menu stuff

# user pages
@users_bp.route('/users')
def show_users():
    # show all users
    users = User.query.all()
    return render_template('users.html', users=users)

@users_bp.route('/users/<int:user_id>')
def user_detail(user_id):
    # show one user details
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user)

# menu and product pages
@products_bp.route('/products')
def show_menu():
    # show pizza menu for ordering
    # Get all the food we sell
    pizzas = Pizza.query.all()
    drinks = Drink.query.all() 
    desserts = Dessert.query.all()
    
    # Get list of customers so they can place orders - fix the tuple unpacking issue
    customers = []
    all_customers = Customer.query.all()
    for customer in all_customers:
        user = User.query.get(customer.user_id)
        if user:  # make sure user exists
            customers.append((customer, user))
    
    return render_template('menu.html', 
                         pizzas=pizzas, 
                         drinks=drinks, 
                         desserts=desserts, 
                         customers=customers)

@products_bp.route('/pizzas')
def show_pizzas():
    # just show pizzas
    pizzas = Pizza.query.all()
    return render_template('pizzas.html', pizzas=pizzas)

# order pages
@orders_bp.route('/orders')
def show_orders():
    # show all orders
    # Update delivery statuses automatically
    update_delivery_statuses()
    
    # Get orders with customer information
    orders = db.session.query(Order, Customer, User)\
        .join(Customer, Order.customer_id == Customer.customer_id)\
        .join(User, Customer.user_id == User.user_id)\
        .order_by(Order.created_at.desc()).all()
    
    return render_template('orders.html', orders=orders)

@orders_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    # show order details
    # Update delivery statuses automatically
    update_delivery_statuses()
    
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
    # make new order
    
    # Get who is ordering
    customer_id = request.form.get('customer_id')
    discount_code = request.form.get('discount_code', '').strip()
    
    if not customer_id:
        flash('Please select a customer!', 'error')
        return redirect(url_for('products.show_menu'))
    
    # Start database transaction explicitly
    try:
        db.session.begin()
        
        # Get customer information
        customer = Customer.query.get(customer_id)
        user = User.query.get(customer.user_id if customer else None)
        
        # Create a new order
        new_order = Order()
        new_order.customer_id = customer_id
        new_order.delivery_status = 'Pending'
        new_order.discount_amount = 0.00
        
        db.session.add(new_order)
        db.session.flush()  # Save to get order ID
        
        # Add items to the order
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
        
        # Calculate discounts
        total_discount = 0.00
        discount_messages = []
        
        # Loyalty discount (10% off for customers with 10+ pizzas, then reset counter)
        loyalty_discount_applied = False
        if customer.is_loyal_customer():
            loyalty_discount = total_price * 0.10
            total_discount += loyalty_discount
            discount_messages.append(f'Loyalty discount: €{loyalty_discount:.2f} (10% off for {customer.total_pizzas_ordered} pizzas ordered!)')
            loyalty_discount_applied = True
        
        # Birthday discount (free cheapest pizza + free drink if ordered)
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
            
            total_discount += birthday_discount
        
        # Discount code
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
        
        # Assign delivery driver
        try:
            # Find an available driver for this postal code area
            driver = Staff.query.join(User).filter(
                Staff.assigned_postal_code == user.postal_code,
                Staff.is_available == True
            ).first()
            
            # Check if driver can deliver now (30-minute rule)
            if driver and driver.can_deliver_now():
                # Assign existing available driver
                new_order.staff_id = driver.staff_id
                new_order.delivery_status = 'In Progress'
                driver.is_available = False
                driver.last_delivery_time = datetime.now()
                
                driver_user = User.query.get(driver.user_id)
                discount_messages.append(f'Driver assigned: {driver_user.get_full_name()}')
            else:
                # No available driver - create a new one
                new_driver_created = create_emergency_driver(user.postal_code)
                
                if new_driver_created:
                    # Assign the newly created driver
                    new_order.staff_id = new_driver_created.staff_id
                    new_order.delivery_status = 'In Progress'
                    new_driver_created.is_available = False
                    new_driver_created.last_delivery_time = datetime.now()
                    
                    new_driver_user = User.query.get(new_driver_created.user_id)
                    discount_messages.append(f'NEW driver created and assigned: {new_driver_user.get_full_name()} for area {user.postal_code}')
        except Exception as e:
            discount_messages.append(f'Driver assignment error: {str(e)}')
        
        # Finalize the order
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
        
        # Show success message
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
    """Enhanced Business Reports Dashboard with detailed analytics"""
    try:
        last_month = datetime.now() - timedelta(days=30)

        # Undelivered Orders (using view if available, fallback to query) 
        try:
            undelivered_orders = db.session.execute(text("""
                SELECT order_id, customer_name, delivery_status,
                       CONCAT(TIMESTAMPDIFF(MINUTE, created_at, NOW()), ' mins') AS waiting_time
                FROM undelivered_orders
            """)).fetchall()
        except:
            # Fallback if view doesn't exist
            undelivered_orders = db.session.query(
                Order.order_id,
                func.concat(User.first_name, ' ', User.last_name).label('customer_name'),
                Order.delivery_status,
                func.concat(func.timestampdiff(text('MINUTE'), Order.created_at, func.now()), ' mins').label('waiting_time')
            ).join(Customer, Customer.customer_id == Order.customer_id)\
             .join(User, User.user_id == Customer.user_id)\
             .filter(Order.delivery_status.in_(['Pending', 'In Progress', 'Out for Delivery'])).all()

        # ---  Top 3 Pizzas Sold (last 30 days) 
        top_pizzas = (
            db.session.query(
                Pizza.name.label('name'),
                func.sum(OrderItem.quantity).label('orders'),
                func.sum(OrderItem.total_price).label('revenue')
            )
            .join(OrderItem, OrderItem.pizza_id == Pizza.pizza_id)
            .join(Order, Order.order_id == OrderItem.order_id)
            .filter(
                OrderItem.item_type == 'Pizza',
                Order.created_at >= last_month
            )
            .group_by(Pizza.pizza_id, Pizza.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(3)
            .all()
        )

        # --- Earnings by Gender ---
        gender_earnings = (
            db.session.query(
                func.coalesce(User.gender, 'Other').label('gender'),
                func.count(Order.order_id).label('orders'),
                func.sum(Order.final_total).label('revenue')
            )
            .join(Customer, Customer.customer_id == Order.customer_id)
            .join(User, User.user_id == Customer.user_id)
            .filter(Order.created_at >= last_month)
            .group_by(User.gender)
            .all()
        )

        # --- Earnings by Age Group ---
        age_diff = func.timestampdiff(text('YEAR'), User.date_of_birth, func.curdate())

        age_group_earnings = (
            db.session.query(
                case(
                    (age_diff < 20, 'Under 20'),
                    ((age_diff >= 20) & (age_diff <= 29), '20-29'),
                    ((age_diff >= 30) & (age_diff <= 39), '30-39'),
                    ((age_diff >= 40) & (age_diff <= 49), '40-49'),
                    (age_diff >= 50, '50+'),
                    else_='Unknown'
                ).label('age_range'),
                func.count(Order.order_id).label('orders'),
                func.sum(Order.final_total).label('revenue')
            )
            .join(Customer, Customer.customer_id == Order.customer_id)
            .join(User, User.user_id == Customer.user_id)
            .filter(Order.created_at >= last_month)
            .group_by('age_range')
            .all()
        )

        # --- Earnings by Postal Code ---
        postal_code_earnings = (
            db.session.query(
                User.postal_code.label('postal_code'),
                func.count(Order.order_id).label('orders'),
                func.sum(Order.final_total).label('revenue')
            )
            .join(Customer, Customer.customer_id == Order.customer_id)
            .join(User, User.user_id == Customer.user_id)
            .filter(Order.created_at >= last_month)
            .group_by(User.postal_code)
            .order_by(func.sum(Order.final_total).desc())
            .limit(10)  # Top 10 postal codes
            .all()
        )

        # ---  Customer Statistics ---
        total_customers = Customer.query.count()
        loyalty_customers = Customer.query.filter(Customer.total_pizzas_ordered >= 10).count()

        # --- Monthly Revenue ---
        monthly_revenue = (
            db.session.query(func.sum(Order.final_total))
            .filter(
                Order.created_at >= last_month,
                Order.delivery_status != 'Cancelled'
            )
            .scalar() or 0
        )

        # Render template with all enhanced datasets
        return render_template(
            'reports.html',
            undelivered_orders=undelivered_orders,
            top_pizzas=top_pizzas,
            gender_earnings=gender_earnings,
            age_group_earnings=age_group_earnings,
            postal_code_earnings=postal_code_earnings,
            total_customers=total_customers,
            loyalty_customers=loyalty_customers,
            monthly_revenue=float(monthly_revenue)
        )
                             
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'error')
        return render_template('reports.html', 
                             undelivered_orders=[],
                             top_pizzas=[],
                             gender_earnings=[],
                             age_group_earnings=[],
                             postal_code_earnings=[],
                             total_customers=0,
                             loyalty_customers=0,
                             monthly_revenue=0.0)

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
            driver.last_delivery_time = datetime.now()
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
    """Show which drivers are available and current delivery progress"""
    try:
        # Update delivery statuses automatically
        update_delivery_statuses()
        
        # Get all delivery staff with their information
        staff_list = []
        all_staff = Staff.query.join(User).all()
        
        for staff in all_staff:
            user = User.query.get(staff.user_id)
            
            # Check availability status
            if staff.can_deliver_now():
                status = 'Available'
            else:
                if staff.last_delivery_time:
                    minutes_left = max(0, 30 - int((datetime.now() - staff.last_delivery_time).total_seconds() / 60))
                    if minutes_left > 0:
                        status = f'Unavailable for {minutes_left} more minutes'
                    else:
                        status = 'Available'
                else:
                    status = 'Available'
            
            # Find current order assigned to this staff member
            current_order = Order.query.filter(
                Order.staff_id == staff.staff_id,
                Order.delivery_status.in_(['In Progress', 'Out for Delivery'])
            ).first()
            
            current_order_info = None
            if current_order:
                customer = Customer.query.get(current_order.customer_id)
                customer_user = User.query.get(customer.user_id)
                
                # Calculate time since order started
                time_elapsed = (datetime.now() - current_order.created_at).total_seconds() / 60
                
                # Determine expected status progression
                if time_elapsed < 0.5:  # Less than 30 seconds
                    expected_next_status = f"Will be 'Out for Delivery' in {int((0.5 - time_elapsed) * 60)} seconds"
                elif time_elapsed < 2:  # Less than 2 minutes
                    expected_next_status = f"Will be 'Delivered' in {int((2 - time_elapsed) * 60)} seconds"
                else:
                    expected_next_status = "Should be delivered (updating...)"
                
                current_order_info = {
                    'order_id': current_order.order_id,
                    'customer_name': customer_user.get_full_name(),
                    'customer_address': customer_user.address,
                    'delivery_status': current_order.delivery_status,
                    'time_elapsed': int(time_elapsed),
                    'expected_next_status': expected_next_status
                }
            
            staff_info = {
                'staff_id': staff.staff_id,
                'staff_name': user.get_full_name(),
                'phone': user.phone,
                'assigned_postal_code': staff.assigned_postal_code,
                'is_available': staff.is_available,
                'last_delivery_time': staff.last_delivery_time,
                'availability_status': status,
                'current_order': current_order_info
            }
            staff_list.append(staff_info)
        
        # Get orders by status for overview
        pending_orders = Order.query.filter_by(delivery_status='Pending').count()
        in_progress_orders = Order.query.filter_by(delivery_status='In Progress').count()
        out_for_delivery_orders = Order.query.filter_by(delivery_status='Out for Delivery').count()
        
        delivery_overview = {
            'pending': pending_orders,
            'in_progress': in_progress_orders,
            'out_for_delivery': out_for_delivery_orders
        }
        
        return render_template('delivery_status.html', 
                             staff_list=staff_list, 
                             delivery_overview=delivery_overview)
        
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

@orders_bp.route('/drivers')
def show_drivers():
    """Show all delivery drivers and their status"""
    try:
        # Get all staff with their user information
        drivers = db.session.query(Staff, User)\
            .join(User, Staff.user_id == User.user_id)\
            .filter(User.user_type == 'Staff')\
            .order_by(Staff.assigned_postal_code, User.first_name).all()
        
        driver_list = []
        for staff, user in drivers:
            # Check availability status
            if staff.can_deliver_now():
                status = 'Available'
                status_class = 'success'
            else:
                if staff.last_delivery_time:
                    minutes_left = max(0, 30 - int((datetime.now() - staff.last_delivery_time).total_seconds() / 60))
                    if minutes_left > 0:
                        status = f'Unavailable ({minutes_left}m left)'
                        status_class = 'warning'
                    else:
                        status = 'Available'
                        status_class = 'success'
                else:
                    status = 'Available'
                    status_class = 'success'
            
            # Check if this is an emergency driver (created automatically)
            is_emergency = '@mammamiapizza.com' in user.email
            
            # Get current orders
            current_orders = Order.query.filter(
                Order.staff_id == staff.staff_id,
                Order.delivery_status.in_(['In Progress', 'Out for Delivery'])
            ).count()
            
            driver_info = {
                'staff_id': staff.staff_id,
                'name': user.get_full_name(),
                'email': user.email,
                'phone': user.phone,
                'postal_code': staff.assigned_postal_code,
                'is_available': staff.is_available,
                'status': status,
                'status_class': status_class,
                'current_orders': current_orders,
                'is_emergency': is_emergency,
                'last_delivery': staff.last_delivery_time
            }
            driver_list.append(driver_info)
        
        return render_template('drivers.html', drivers=driver_list)
        
    except Exception as e:
        flash(f'Error loading drivers: {str(e)}', 'error')
        return redirect(url_for('orders.show_orders'))

@orders_bp.route('/admin/create-driver', methods=['POST'])
def manual_create_driver():
    """Manually create a new driver for testing"""
    try:
        postal_code = request.form.get('postal_code', '20121')
        
        new_driver = create_emergency_driver(postal_code)
        
        if new_driver:
            db.session.commit()
            new_user = User.query.get(new_driver.user_id)
            flash(f'✅ New driver created: {new_user.get_full_name()} for area {postal_code}', 'success')
        else:
            flash('❌ Failed to create new driver', 'error')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating driver: {str(e)}', 'error')
    
    return redirect(url_for('orders.show_drivers'))