from flask import render_template, redirect, url_for, request, flash, jsonify
from . import user_bp
from database import execute_query, get_db_connection, get_db_cursor
from datetime import datetime

# User routes - Web interface
@user_bp.route('/')
def index():
    # Get all users with direct SQL
    users = execute_query("""
        SELECT u.*, 
               CASE WHEN a.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_agent_profile,
               CASE WHEN r.user_id IS NOT NULL THEN TRUE ELSE FALSE END as has_renter_profile
        FROM "User" u
        LEFT JOIN Agent a ON u.ID = a.user_id
        LEFT JOIN Prospective_Renters r ON u.ID = r.user_id
        ORDER BY u.ID
    """)
    return render_template('users/index.html', users=users)

@user_bp.route('/new')
def new():
    return render_template('users/new.html')

@user_bp.route('/create', methods=['POST'])
def create():
    # Use a database transaction
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Create the user
        cursor.execute("""
            INSERT INTO "User" (email, name, is_agent)
            VALUES (%s, %s, %s)
            RETURNING ID
        """, (
            request.form['email'],
            request.form['name'],
            bool(request.form.get('is_agent', False))
        ))
        
        user_id = cursor.fetchone()[0]
        
        # Create address for the user
        cursor.execute("""
            INSERT INTO Address (user_id, street, city, state, zip_code, country)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            request.form['street'],
            request.form['city'],
            request.form['state'],
            request.form['zip_code'],
            request.form['country']
        ))
        
        # If user is an agent, create agent profile
        if bool(request.form.get('is_agent')):
            cursor.execute("""
                INSERT INTO Agent (user_id, job_title, real_estate_agency, contact_info)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                request.form.get('job_title', ''),
                request.form.get('real_estate_agency', ''),
                request.form.get('contact_info', '')
            ))
        # If user is a renter, create renter profile
        else:
            # Parse the date if provided, otherwise use None
            move_in_date = None
            if request.form.get('desired_move_in_date'):
                move_in_date = datetime.strptime(request.form['desired_move_in_date'], '%Y-%m-%d').date()
            
            cursor.execute("""
                INSERT INTO Prospective_Renters (user_id, desired_move_in_date, preferred_location, budget)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                move_in_date,
                request.form.get('preferred_location', ''),
                request.form.get('budget', 0)
            ))
            
            # Create reward program for renter
            cursor.execute("""
                INSERT INTO Reward_Program (renter_id, reward_points)
                VALUES (%s, %s)
            """, (
                user_id,
                0  # Initial reward points
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('User created successfully!', 'success')
        return redirect(url_for('user.index'))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error creating user: {str(e)}', 'danger')
        return redirect(url_for('user.new'))
    finally:
        cursor.close()

# API routes for User
@user_bp.route('/api/users', methods=['POST'])
def api_create_user():
    # Use a database transaction
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        data = request.json
        
        # Start transaction
        cursor.execute("BEGIN")
        
        # Create the user
        cursor.execute("""
            INSERT INTO "User" (email, name, is_agent)
            VALUES (%s, %s, %s)
            RETURNING ID
        """, (
            data['email'],
            data['name'],
            data.get('is_agent', False)
        ))
        
        user_id = cursor.fetchone()[0]
        
        # Create address for the user if provided
        if 'address' in data:
            cursor.execute("""
                INSERT INTO Address (user_id, street, city, state, zip_code, country)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                data['address']['street'],
                data['address']['city'],
                data['address']['state'],
                data['address']['zip_code'],
                data['address']['country']
            ))
        
        # If user is an agent, create agent profile
        if data.get('is_agent') and 'agent_details' in data:
            cursor.execute("""
                INSERT INTO Agent (user_id, job_title, real_estate_agency, contact_info)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                data['agent_details'].get('job_title', ''),
                data['agent_details'].get('real_estate_agency', ''),
                data['agent_details'].get('contact_info', '')
            ))
        # If user is a renter, create renter profile
        elif not data.get('is_agent') and 'renter_details' in data:
            # Parse the date if provided, otherwise use None
            move_in_date = None
            if data['renter_details'].get('desired_move_in_date'):
                move_in_date = datetime.strptime(data['renter_details']['desired_move_in_date'], '%Y-%m-%d').date()
            
            cursor.execute("""
                INSERT INTO Prospective_Renters (user_id, desired_move_in_date, preferred_location, budget)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                move_in_date,
                data['renter_details'].get('preferred_location', ''),
                data['renter_details'].get('budget', 0)
            ))
            
            # Create reward program for renter
            cursor.execute("""
                INSERT INTO Reward_Program (renter_id, reward_points)
                VALUES (%s, %s)
            """, (
                user_id,
                0  # Initial reward points
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User created successfully!'
        }), 201
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    finally:
        cursor.close()

# API routes for CreditCard
@user_bp.route('/api/users/<int:user_id>/credit-cards', methods=['POST'])
def api_create_credit_card(user_id):
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        data = request.json
        
        # Check if user exists
        cursor.execute("""
            SELECT ID FROM "User" WHERE ID = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Start transaction
        cursor.execute("BEGIN")
        
        # Create credit card
        cursor.execute("""
            INSERT INTO Credit_Card (user_id, card_number, expiration_date, payment_address_id)
            VALUES (%s, %s, %s, %s)
            RETURNING ID
        """, (
            user_id,
            data['card_number'],
            datetime.strptime(data['expiration_date'], '%Y-%m-%d').date(),
            data.get('payment_address_id')
        ))
        
        card_id = cursor.fetchone()[0]
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        return jsonify({
            'success': True,
            'credit_card_id': card_id,
            'message': 'Credit card added successfully!'
        }), 201
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    finally:
        cursor.close()

# User Detail Route
@user_bp.route('/<int:user_id>')
def detail(user_id):
    # Get user details with direct SQL
    user_data = execute_query("""
        SELECT u.* 
        FROM "User" u
        WHERE u.ID = %s
    """, (user_id,), fetchone=True)
    
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('user.index'))
    
    # Get user addresses
    addresses = execute_query("""
        SELECT * FROM Address WHERE user_id = %s
    """, (user_id,))
    
    # Get credit cards
    credit_cards = execute_query("""
        SELECT cc.*, a.street, a.city, a.state
        FROM Credit_Card cc
        LEFT JOIN Address a ON cc.payment_address_id = a.ID
        WHERE cc.user_id = %s
    """, (user_id,))
    
    # Check if user is an agent or renter
    agent_data = None
    renter_data = None
    reward_points = None
    bookings = None
    
    if user_data['is_agent']:
        agent_data = execute_query("""
            SELECT * FROM Agent WHERE user_id = %s
        """, (user_id,), fetchone=True)
    else:
        renter_data = execute_query("""
            SELECT * FROM Prospective_Renters WHERE user_id = %s
        """, (user_id,), fetchone=True)
        
        reward_points = execute_query("""
            SELECT reward_points FROM Reward_Program WHERE renter_id = %s
        """, (user_id,), fetchone=True)
        
        bookings = execute_query("""
            SELECT b.*, p.location, p.city, p.state, p.price
            FROM Booking b
            JOIN Property p ON b.property_id = p.ID
            WHERE b.renter_id = %s
            ORDER BY b.start_date DESC
        """, (user_id,))
    
    return render_template('users/detail.html', 
                          user=user_data, 
                          addresses=addresses,
                          credit_cards=credit_cards,
                          agent_data=agent_data,
                          renter_data=renter_data,
                          reward_points=reward_points,
                          bookings=bookings)

@user_bp.route('/<int:user_id>/edit')
def edit(user_id):
    # Get user details
    user_data = execute_query("""
        SELECT * FROM "User" WHERE ID = %s
    """, (user_id,), fetchone=True)
    
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('user.index'))
    
    # Get user addresses
    addresses = execute_query("""
        SELECT * FROM Address WHERE user_id = %s
    """, (user_id,))
    
    # Check if user is an agent or renter
    agent_data = None
    renter_data = None
    
    if user_data['is_agent']:
        agent_data = execute_query("""
            SELECT * FROM Agent WHERE user_id = %s
        """, (user_id,), fetchone=True)
    else:
        renter_data = execute_query("""
            SELECT * FROM Prospective_Renters WHERE user_id = %s
        """, (user_id,), fetchone=True)
        
        reward_data = execute_query("""
            SELECT reward_points FROM Reward_Program WHERE renter_id = %s
        """, (user_id,), fetchone=True)
        
        if reward_data:
            renter_data['reward_points'] = reward_data['reward_points']
    
    return render_template('users/edit.html', 
                          user=user_data, 
                          addresses=addresses,
                          agent_data=agent_data,
                          renter_data=renter_data)

@user_bp.route('/<int:user_id>/update', methods=['POST'])
def update(user_id):
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Get current user info
        cursor.execute("""
            SELECT is_agent FROM "User" WHERE ID = %s
        """, (user_id,))
        
        current_user = cursor.fetchone()
        if not current_user:
            raise ValueError("User not found")
            
        current_is_agent = current_user['is_agent']
        new_is_agent = bool(request.form.get('is_agent', False))
        
        # Update the user
        cursor.execute("""
            UPDATE "User"
            SET email = %s,
                name = %s,
                is_agent = %s
            WHERE ID = %s
        """, (
            request.form['email'],
            request.form['name'],
            new_is_agent,
            user_id
        ))
        
        # Handle changing user type (agent to renter or vice versa)
        if current_is_agent != new_is_agent:
            if new_is_agent:
                # Changing from renter to agent
                # Delete renter data
                cursor.execute("DELETE FROM Reward_Program WHERE renter_id = %s", (user_id,))
                cursor.execute("DELETE FROM Prospective_Renters WHERE user_id = %s", (user_id,))
                
                # Create agent data
                cursor.execute("""
                    INSERT INTO Agent (user_id, job_title, real_estate_agency, contact_info)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_id,
                    request.form.get('job_title', ''),
                    request.form.get('real_estate_agency', ''),
                    request.form.get('contact_info', '')
                ))
            else:
                # Changing from agent to renter
                # Delete agent data
                cursor.execute("DELETE FROM Agent WHERE user_id = %s", (user_id,))
                
                # Create renter data
                # Parse the date if provided, otherwise use None
                move_in_date = None
                if request.form.get('desired_move_in_date'):
                    move_in_date = datetime.strptime(request.form['desired_move_in_date'], '%Y-%m-%d').date()
                
                cursor.execute("""
                    INSERT INTO Prospective_Renters (user_id, desired_move_in_date, preferred_location, budget)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_id,
                    move_in_date,
                    request.form.get('preferred_location', ''),
                    request.form.get('budget', 0)
                ))
                
                # Create reward program for renter
                cursor.execute("""
                    INSERT INTO Reward_Program (renter_id, reward_points)
                    VALUES (%s, %s)
                """, (
                    user_id,
                    0  # Initial reward points
                ))
        else:
            # Just update the existing profile
            if new_is_agent:
                cursor.execute("""
                    UPDATE Agent
                    SET job_title = %s,
                        real_estate_agency = %s,
                        contact_info = %s
                    WHERE user_id = %s
                """, (
                    request.form.get('job_title', ''),
                    request.form.get('real_estate_agency', ''),
                    request.form.get('contact_info', ''),
                    user_id
                ))
            else:
                # Parse the date if provided, otherwise use None
                move_in_date = None
                if request.form.get('desired_move_in_date'):
                    move_in_date = datetime.strptime(request.form['desired_move_in_date'], '%Y-%m-%d').date()
                
                cursor.execute("""
                    UPDATE Prospective_Renters
                    SET desired_move_in_date = %s,
                        preferred_location = %s,
                        budget = %s
                    WHERE user_id = %s
                """, (
                    move_in_date,
                    request.form.get('preferred_location', ''),
                    request.form.get('budget', 0),
                    user_id
                ))
                
                # Update reward points
                try:
                    reward_points = int(request.form.get('reward_points', 0))
                except (ValueError, TypeError):
                    reward_points = 0
                    
                cursor.execute("""
                    UPDATE Reward_Program
                    SET reward_points = %s
                    WHERE renter_id = %s
                """, (
                    reward_points,
                    user_id
                ))
        
        # Update address if provided
        if 'primary_address_id' in request.form and request.form['primary_address_id']:
            address_id = int(request.form['primary_address_id'])
            cursor.execute("""
                UPDATE Address
                SET street = %s,
                    city = %s,
                    state = %s,
                    zip_code = %s,
                    country = %s
                WHERE ID = %s AND user_id = %s
            """, (
                request.form['street'],
                request.form['city'],
                request.form['state'],
                request.form['zip_code'],
                request.form['country'],
                address_id,
                user_id
            ))
        else:
            # Create new address
            cursor.execute("""
                INSERT INTO Address (user_id, street, city, state, zip_code, country)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                request.form['street'],
                request.form['city'],
                request.form['state'],
                request.form['zip_code'],
                request.form['country']
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('user.detail', user_id=user_id))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error updating user: {str(e)}', 'danger')
        return redirect(url_for('user.edit', user_id=user_id))
    finally:
        cursor.close()

@user_bp.route('/<int:user_id>/delete', methods=['POST'])
def delete(user_id):
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Check if user has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM Booking WHERE renter_id = %s
        """, (user_id,))
        
        booking_count = cursor.fetchone()[0]
        
        if booking_count > 0:
            flash('Cannot delete user with existing bookings.', 'danger')
            return redirect(url_for('user.detail', user_id=user_id))
            
        # Get user type
        cursor.execute("""
            SELECT is_agent FROM "User" WHERE ID = %s
        """, (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            raise ValueError("User not found")
            
        is_agent = user_data['is_agent']
        
        # Delete related data based on user type
        if is_agent:
            cursor.execute("DELETE FROM Agent WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM Reward_Program WHERE renter_id = %s", (user_id,))
            cursor.execute("DELETE FROM Prospective_Renters WHERE user_id = %s", (user_id,))
            
        # Delete credit cards
        cursor.execute("DELETE FROM Credit_Card WHERE user_id = %s", (user_id,))
        
        # Delete addresses
        cursor.execute("DELETE FROM Address WHERE user_id = %s", (user_id,))
        
        # Delete the user
        cursor.execute("DELETE FROM \"User\" WHERE ID = %s", (user_id,))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('User deleted successfully!', 'success')
        return redirect(url_for('user.index'))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error deleting user: {str(e)}', 'danger')
        return redirect(url_for('user.detail', user_id=user_id))
    finally:
        cursor.close()