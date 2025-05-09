import psycopg2
import psycopg2.extras
from config import Config
from flask import g, current_app

def get_db_connection():
    """Get a database connection from Flask's g object or create a new one"""
    if 'db' not in g:
        g.db = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        # Enable autocommit
        g.db.autocommit = False
        
    return g.db

def get_db_cursor(cursor_factory=psycopg2.extras.DictCursor):
    """Get a database cursor with the specified cursor factory"""
    conn = get_db_connection()
    return conn.cursor(cursor_factory=cursor_factory)

def close_db(e=None):
    """Close the database connection"""
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def init_app(app):
    """Initialize the database connection with the Flask app"""
    # Register close_db to run when the request context ends
    app.teardown_appcontext(close_db)
    
    # Initialize the database schema if needed
    with app.app_context():
        # This function will only be called once when the app starts
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if at least one table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'User'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            app.logger.info("Database tables don't exist. Creating schema...")
            create_schema(conn)
            app.logger.info("Schema created successfully!")
        
        cursor.close()

def create_schema(conn):
    """Create the database schema"""
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    -- User & Related Entities
    CREATE TABLE "User" (
        ID SERIAL PRIMARY KEY,
        email VARCHAR(255),
        name VARCHAR(255),
        is_agent BOOLEAN
    );
    
    -- Create an index on User.email
    CREATE INDEX idx_user_email ON "User"(email);
    
    CREATE TABLE Agent (
        user_id INTEGER PRIMARY KEY REFERENCES "User"(ID),
        job_title VARCHAR(255),
        real_estate_agency VARCHAR(255),
        contact_info TEXT
    );
    
    CREATE TABLE Prospective_Renters (
        user_id INTEGER PRIMARY KEY REFERENCES "User"(ID),
        desired_move_in_date DATE,
        preferred_location VARCHAR(255),
        budget DECIMAL
    );
    
    CREATE TABLE Address (
        ID SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES "User"(ID),
        street VARCHAR(255),
        city VARCHAR(255),
        state VARCHAR(255),
        zip_code VARCHAR(10),
        country VARCHAR(100)
    );
    
    CREATE TABLE Reward_Program (
        renter_id INTEGER PRIMARY KEY REFERENCES "User"(ID),
        reward_points INTEGER
    );
    
    CREATE TABLE Credit_Card (
        ID SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES "User"(ID),
        card_number VARCHAR(20),
        expiration_date DATE,
        payment_address_id INTEGER REFERENCES Address(ID)
    );
    
    -- Neighborhood
    CREATE TABLE Neighborhood (
        ID SERIAL PRIMARY KEY,
        location VARCHAR(255),
        city VARCHAR(255),
        state VARCHAR(255),
        crime_rate FLOAT,
        nearby_schools TEXT
    );
    
    -- Property and Subtypes
    CREATE TABLE Property (
        ID SERIAL PRIMARY KEY,
        type VARCHAR(50),
        description TEXT,
        location VARCHAR(255),
        city VARCHAR(100),
        state VARCHAR(100),
        price DECIMAL,
        is_avail BOOLEAN,
        neighborhood_id INTEGER REFERENCES Neighborhood(ID)
    );
    
    CREATE TABLE House (
        property_id INTEGER PRIMARY KEY REFERENCES Property(ID),
        num_rooms INTEGER,
        square_footage INTEGER
    );
    
    CREATE TABLE Apartment (
        property_id INTEGER PRIMARY KEY REFERENCES Property(ID),
        num_rooms INTEGER,
        square_footage INTEGER,
        building_type VARCHAR(100)
    );
    
    CREATE TABLE Commercial_Building (
        property_id INTEGER PRIMARY KEY REFERENCES Property(ID),
        square_footage INTEGER,
        business_type VARCHAR(100)
    );
    
    CREATE TABLE Vacation_Home (
        property_id INTEGER PRIMARY KEY REFERENCES Property(ID),
        square_footage INTEGER,
        amenities TEXT,
        max_occupancy INTEGER,
        is_seasonal BOOLEAN
    );
    
    CREATE TABLE Land (
        property_id INTEGER PRIMARY KEY REFERENCES Property(ID),
        acreage DECIMAL,
        utilities TEXT
    );
    
    -- Booking
    CREATE TABLE Booking (
        ID SERIAL PRIMARY KEY,
        renter_id INTEGER REFERENCES "User"(ID),
        property_id INTEGER REFERENCES Property(ID),
        card_id INTEGER REFERENCES Credit_Card(ID),
        booking_date DATE,
        total_amount DECIMAL,
        start_date DATE,
        end_date DATE,
        is_canceled BOOLEAN
    );
    """)
    
    conn.commit()
    cursor.close()

def execute_query(query, params=None, fetchone=False, commit=False):
    """
    Execute a database query
    
    Parameters:
    - query: SQL query string
    - params: Parameters for the query (tuple or dictionary)
    - fetchone: If True, fetches only one result
    - commit: If True, commits the transaction
    
    Returns:
    - Query results or None if no results
    """
    conn = get_db_connection()
    cursor = get_db_cursor()
    
    try:
        cursor.execute(query, params)
        
        if query.strip().upper().startswith(('SELECT', 'RETURNING')):
            if fetchone:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        else:
            result = None
            
        if commit:
            conn.commit()
            
        return result
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()