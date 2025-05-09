from flask import render_template, redirect, url_for, request, flash, jsonify
from . import property_bp
from database import execute_query, get_db_connection, get_db_cursor
from datetime import datetime

# Property routes - Web interface
@property_bp.route('/')
def index():
    # Get all properties with direct SQL
    properties = execute_query("""
        SELECT p.*, 
               n.location as neighborhood_location,
               n.city as neighborhood_city,
               CASE
                   WHEN h.property_id IS NOT NULL THEN 'House'
                   WHEN a.property_id IS NOT NULL THEN 'Apartment'
                   WHEN c.property_id IS NOT NULL THEN 'Commercial'
                   WHEN v.property_id IS NOT NULL THEN 'Vacation'
                   WHEN l.property_id IS NOT NULL THEN 'Land'
                   ELSE 'Unknown'
               END as property_subtype
        FROM Property p
        LEFT JOIN Neighborhood n ON p.neighborhood_id = n.ID
        LEFT JOIN House h ON p.ID = h.property_id
        LEFT JOIN Apartment a ON p.ID = a.property_id
        LEFT JOIN Commercial_Building c ON p.ID = c.property_id
        LEFT JOIN Vacation_Home v ON p.ID = v.property_id
        LEFT JOIN Land l ON p.ID = l.property_id
        ORDER BY p.ID
    """)
    return render_template('properties/index.html', properties=properties)

@property_bp.route('/new')
def new():
    # Get all neighborhoods for the dropdown
    neighborhoods = execute_query("""
        SELECT * FROM Neighborhood
        ORDER BY location, city
    """)
    return render_template('properties/new.html', neighborhoods=neighborhoods)

@property_bp.route('/create', methods=['POST'])
def create():
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Create base property
        property_type = request.form['type']
        
        # Safely convert price to numeric with fallback
        try:
            price = float(request.form['price'])
        except (ValueError, TypeError):
            price = 0.0
            
        # Get neighborhood_id safely
        neighborhood_id = request.form.get('neighborhood_id')
        if neighborhood_id == '':
            neighborhood_id = None
        
        cursor.execute("""
            INSERT INTO Property (type, description, location, city, state, price, is_avail, neighborhood_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ID
        """, (
            property_type,
            request.form['description'],
            request.form['location'],
            request.form['city'],
            request.form['state'],
            price,
            bool(request.form.get('is_avail', True)),
            neighborhood_id
        ))
        
        property_id = cursor.fetchone()[0]
        
        # Create the specific property type
        if property_type == 'house':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(request.form.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            cursor.execute("""
                INSERT INTO House (property_id, num_rooms, square_footage)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                num_rooms,
                square_footage
            ))
        elif property_type == 'apartment':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(request.form.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            building_type = request.form.get('building_type', '')
            
            cursor.execute("""
                INSERT INTO Apartment (property_id, num_rooms, square_footage, building_type)
                VALUES (%s, %s, %s, %s)
            """, (
                property_id,
                num_rooms,
                square_footage,
                building_type
            ))
        elif property_type == 'commercial':
            # Safe conversion of numeric fields
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            business_type = request.form.get('business_type', '')
            
            cursor.execute("""
                INSERT INTO Commercial_Building (property_id, square_footage, business_type)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                square_footage,
                business_type
            ))
        elif property_type == 'vacation':
            # Safe conversion of numeric fields
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            try:
                max_occupancy = int(request.form.get('max_occupancy', 0))
            except (ValueError, TypeError):
                max_occupancy = 0
                
            amenities = request.form.get('amenities', '')
            is_seasonal = bool(request.form.get('is_seasonal', False))
            
            cursor.execute("""
                INSERT INTO Vacation_Home (property_id, square_footage, amenities, max_occupancy, is_seasonal)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                property_id,
                square_footage,
                amenities,
                max_occupancy,
                is_seasonal
            ))
        elif property_type == 'land':
            # Safe conversion of numeric fields
            try:
                acreage = float(request.form.get('acreage', 0))
            except (ValueError, TypeError):
                acreage = 0.0
                
            utilities = request.form.get('utilities', '')
            
            cursor.execute("""
                INSERT INTO Land (property_id, acreage, utilities)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                acreage,
                utilities
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('Property created successfully!', 'success')
        return redirect(url_for('property.index'))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error creating property: {str(e)}', 'danger')
        return redirect(url_for('property.new'))
    finally:
        cursor.close()

# API routes for Neighborhood
@property_bp.route('/api/neighborhoods', methods=['POST'])
def api_create_neighborhood():
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        data = request.json
        
        cursor.execute("""
            INSERT INTO Neighborhood (location, city, state, crime_rate, nearby_schools)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING ID
        """, (
            data['location'],
            data['city'],
            data['state'],
            data.get('crime_rate'),
            data.get('nearby_schools', '')
        ))
        
        neighborhood_id = cursor.fetchone()[0]
        conn.commit()
        
        return jsonify({
            'success': True,
            'neighborhood_id': neighborhood_id,
            'message': 'Neighborhood created successfully!'
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    finally:
        cursor.close()

# API routes for Property
@property_bp.route('/api/properties', methods=['POST'])
def api_create_property():
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        data = request.json
        
        # Start transaction
        cursor.execute("BEGIN")
        
        # Create base property
        property_type = data['type']
        
        # Safely convert price to numeric with fallback
        try:
            price = float(data['price'])
        except (ValueError, TypeError):
            price = 0.0
            
        # Get neighborhood_id safely
        neighborhood_id = data.get('neighborhood_id')
        if neighborhood_id == '':
            neighborhood_id = None
            
        cursor.execute("""
            INSERT INTO Property (type, description, location, city, state, price, is_avail, neighborhood_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ID
        """, (
            property_type,
            data['description'],
            data['location'],
            data['city'],
            data['state'],
            price,
            data.get('is_avail', True),
            neighborhood_id
        ))
        
        property_id = cursor.fetchone()[0]
        
        # Create the specific property type
        if property_type == 'house':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(data.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(data.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            cursor.execute("""
                INSERT INTO House (property_id, num_rooms, square_footage)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                num_rooms,
                square_footage
            ))
        elif property_type == 'apartment':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(data.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(data.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            building_type = data.get('building_type', '')
            
            cursor.execute("""
                INSERT INTO Apartment (property_id, num_rooms, square_footage, building_type)
                VALUES (%s, %s, %s, %s)
            """, (
                property_id,
                num_rooms,
                square_footage,
                building_type
            ))
        elif property_type == 'commercial':
            # Safe conversion of numeric fields
            try:
                square_footage = int(data.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            business_type = data.get('business_type', '')
            
            cursor.execute("""
                INSERT INTO Commercial_Building (property_id, square_footage, business_type)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                square_footage,
                business_type
            ))
        elif property_type == 'vacation':
            # Safe conversion of numeric fields
            try:
                square_footage = int(data.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            try:
                max_occupancy = int(data.get('max_occupancy', 0))
            except (ValueError, TypeError):
                max_occupancy = 0
                
            amenities = data.get('amenities', '')
            is_seasonal = bool(data.get('is_seasonal', False))
            
            cursor.execute("""
                INSERT INTO Vacation_Home (property_id, square_footage, amenities, max_occupancy, is_seasonal)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                property_id,
                square_footage,
                amenities,
                max_occupancy,
                is_seasonal
            ))
        elif property_type == 'land':
            # Safe conversion of numeric fields
            try:
                acreage = float(data.get('acreage', 0))
            except (ValueError, TypeError):
                acreage = 0.0
                
            utilities = data.get('utilities', '')
            
            cursor.execute("""
                INSERT INTO Land (property_id, acreage, utilities)
                VALUES (%s, %s, %s)
            """, (
                property_id,
                acreage,
                utilities
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        return jsonify({
            'success': True,
            'property_id': property_id,
            'message': 'Property created successfully!'
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

# API routes for Booking
@property_bp.route('/api/bookings', methods=['POST'])
def api_create_booking():
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        data = request.json
        
        # Validate that property is available
        cursor.execute("""
            SELECT is_avail FROM Property WHERE ID = %s
        """, (data['property_id'],))
        
        property_result = cursor.fetchone()
        if not property_result or not property_result[0]:
            return jsonify({
                'success': False,
                'error': 'Property is not available for booking'
            }), 400
        
        # Start transaction
        cursor.execute("BEGIN")
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Create the booking
        cursor.execute("""
            INSERT INTO Booking (renter_id, property_id, card_id, total_amount, start_date, end_date, is_canceled, booking_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ID
        """, (
            data['renter_id'],
            data['property_id'],
            data['card_id'],
            data['total_amount'],
            start_date,
            end_date,
            False,  # is_canceled defaults to false
            datetime.now().date()  # booking_date is set to current date
        ))
        
        booking_id = cursor.fetchone()[0]
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'message': 'Booking created successfully!'
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

# Property Detail Route
@property_bp.route('/<int:property_id>')
def detail(property_id):
    # Get property details with direct SQL
    property_data = execute_query("""
        SELECT p.*, 
               n.location as neighborhood_location,
               n.city as neighborhood_city,
               n.state as neighborhood_state
        FROM Property p
        LEFT JOIN Neighborhood n ON p.neighborhood_id = n.ID
        WHERE p.ID = %s
    """, (property_id,), fetchone=True)
    
    if not property_data:
        flash('Property not found.', 'danger')
        return redirect(url_for('property.index'))
    
    # Get specific property type details
    property_type = property_data['type']
    
    if property_type == 'house':
        specific_data = execute_query("""
            SELECT * FROM House WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'apartment':
        specific_data = execute_query("""
            SELECT * FROM Apartment WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'commercial':
        specific_data = execute_query("""
            SELECT * FROM Commercial_Building WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'vacation':
        specific_data = execute_query("""
            SELECT * FROM Vacation_Home WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'land':
        specific_data = execute_query("""
            SELECT * FROM Land WHERE property_id = %s
        """, (property_id,), fetchone=True)
    else:
        specific_data = None
    
    # Get booking history for this property
    bookings = execute_query("""
        SELECT b.*, u.name as renter_name
        FROM Booking b
        JOIN "User" u ON b.renter_id = u.ID
        WHERE b.property_id = %s
        ORDER BY b.start_date DESC
    """, (property_id,))
    
    return render_template('properties/detail.html', 
                          property=property_data, 
                          specific_data=specific_data,
                          bookings=bookings)

# Property Update Route
@property_bp.route('/<int:property_id>/edit')
def edit(property_id):
    # Get property details
    property_data = execute_query("""
        SELECT * FROM Property WHERE ID = %s
    """, (property_id,), fetchone=True)
    
    if not property_data:
        flash('Property not found.', 'danger')
        return redirect(url_for('property.index'))
    
    # Get all neighborhoods for dropdown
    neighborhoods = execute_query("""
        SELECT * FROM Neighborhood ORDER BY location, city
    """)
    
    # Get specific property type details
    property_type = property_data['type']
    
    if property_type == 'house':
        specific_data = execute_query("""
            SELECT * FROM House WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'apartment':
        specific_data = execute_query("""
            SELECT * FROM Apartment WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'commercial':
        specific_data = execute_query("""
            SELECT * FROM Commercial_Building WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'vacation':
        specific_data = execute_query("""
            SELECT * FROM Vacation_Home WHERE property_id = %s
        """, (property_id,), fetchone=True)
    elif property_type == 'land':
        specific_data = execute_query("""
            SELECT * FROM Land WHERE property_id = %s
        """, (property_id,), fetchone=True)
    else:
        specific_data = None
    
    return render_template('properties/edit.html', 
                          property=property_data, 
                          specific_data=specific_data,
                          neighborhoods=neighborhoods)

@property_bp.route('/<int:property_id>/update', methods=['POST'])
def update(property_id):
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Safely convert price to numeric with fallback
        try:
            price = float(request.form['price'])
        except (ValueError, TypeError):
            price = 0.0
            
        # Get neighborhood_id safely
        neighborhood_id = request.form.get('neighborhood_id')
        if neighborhood_id == '':
            neighborhood_id = None
            
        # Update base property
        cursor.execute("""
            UPDATE Property
            SET description = %s,
                location = %s,
                city = %s,
                state = %s,
                price = %s,
                is_avail = %s,
                neighborhood_id = %s
            WHERE ID = %s
        """, (
            request.form['description'],
            request.form['location'],
            request.form['city'],
            request.form['state'],
            price,
            bool(request.form.get('is_avail', False)),
            neighborhood_id,
            property_id
        ))
        
        # Update specific property type
        property_type = request.form['type']
        
        if property_type == 'house':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(request.form.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            cursor.execute("""
                UPDATE House
                SET num_rooms = %s,
                    square_footage = %s
                WHERE property_id = %s
            """, (
                num_rooms,
                square_footage,
                property_id
            ))
        elif property_type == 'apartment':
            # Safe conversion of numeric fields
            try:
                num_rooms = int(request.form.get('num_rooms', 0))
            except (ValueError, TypeError):
                num_rooms = 0
                
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            building_type = request.form.get('building_type', '')
            
            cursor.execute("""
                UPDATE Apartment
                SET num_rooms = %s,
                    square_footage = %s,
                    building_type = %s
                WHERE property_id = %s
            """, (
                num_rooms,
                square_footage,
                building_type,
                property_id
            ))
        elif property_type == 'commercial':
            # Safe conversion of numeric fields
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            business_type = request.form.get('business_type', '')
            
            cursor.execute("""
                UPDATE Commercial_Building
                SET square_footage = %s,
                    business_type = %s
                WHERE property_id = %s
            """, (
                square_footage,
                business_type,
                property_id
            ))
        elif property_type == 'vacation':
            # Safe conversion of numeric fields
            try:
                square_footage = int(request.form.get('square_footage', 0))
            except (ValueError, TypeError):
                square_footage = 0
                
            try:
                max_occupancy = int(request.form.get('max_occupancy', 0))
            except (ValueError, TypeError):
                max_occupancy = 0
                
            amenities = request.form.get('amenities', '')
            is_seasonal = bool(request.form.get('is_seasonal', False))
            
            cursor.execute("""
                UPDATE Vacation_Home
                SET square_footage = %s,
                    amenities = %s,
                    max_occupancy = %s,
                    is_seasonal = %s
                WHERE property_id = %s
            """, (
                square_footage,
                amenities,
                max_occupancy,
                is_seasonal,
                property_id
            ))
        elif property_type == 'land':
            # Safe conversion of numeric fields
            try:
                acreage = float(request.form.get('acreage', 0))
            except (ValueError, TypeError):
                acreage = 0.0
                
            utilities = request.form.get('utilities', '')
            
            cursor.execute("""
                UPDATE Land
                SET acreage = %s,
                    utilities = %s
                WHERE property_id = %s
            """, (
                acreage,
                utilities,
                property_id
            ))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('Property updated successfully!', 'success')
        return redirect(url_for('property.detail', property_id=property_id))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error updating property: {str(e)}', 'danger')
        return redirect(url_for('property.edit', property_id=property_id))
    finally:
        cursor.close()

# Property Delete Route
@property_bp.route('/<int:property_id>/delete', methods=['POST'])
def delete(property_id):
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Check if property has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM Booking WHERE property_id = %s
        """, (property_id,))
        
        booking_count = cursor.fetchone()[0]
        
        if booking_count > 0:
            flash('Cannot delete property with existing bookings.', 'danger')
            return redirect(url_for('property.detail', property_id=property_id))
            
        # Get property type
        cursor.execute("""
            SELECT type FROM Property WHERE ID = %s
        """, (property_id,))
        
        property_type = cursor.fetchone()[0]
        
        # Delete specific property type
        if property_type == 'house':
            cursor.execute("DELETE FROM House WHERE property_id = %s", (property_id,))
        elif property_type == 'apartment':
            cursor.execute("DELETE FROM Apartment WHERE property_id = %s", (property_id,))
        elif property_type == 'commercial':
            cursor.execute("DELETE FROM Commercial_Building WHERE property_id = %s", (property_id,))
        elif property_type == 'vacation':
            cursor.execute("DELETE FROM Vacation_Home WHERE property_id = %s", (property_id,))
        elif property_type == 'land':
            cursor.execute("DELETE FROM Land WHERE property_id = %s", (property_id,))
        
        # Delete base property
        cursor.execute("DELETE FROM Property WHERE ID = %s", (property_id,))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        flash('Property deleted successfully!', 'success')
        return redirect(url_for('property.index'))
    except Exception as e:
        # Rollback in case of error
        cursor.execute("ROLLBACK")
        flash(f'Error deleting property: {str(e)}', 'danger')
        return redirect(url_for('property.detail', property_id=property_id))
    finally:
        cursor.close()