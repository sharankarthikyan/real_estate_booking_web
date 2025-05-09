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