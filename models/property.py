from datetime import datetime
from . import db

class Neighborhood(db.Model):
    __tablename__ = 'Neighborhood'
    
    ID = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    crime_rate = db.Column(db.Float)
    nearby_schools = db.Column(db.Text)
    
    # Relationship to properties
    properties = db.relationship('Property', backref='neighborhood')
    
    def __repr__(self):
        return f'<Neighborhood {self.ID}: {self.location}, {self.city}>'

class Property(db.Model):
    __tablename__ = 'Property'
    
    ID = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    price = db.Column(db.Numeric)
    is_avail = db.Column(db.Boolean)
    neighborhood_id = db.Column(db.Integer, db.ForeignKey('Neighborhood.ID'))
    
    # Relationship to bookings
    bookings = db.relationship('Booking', backref='property')
    
    def __repr__(self):
        return f'<Property {self.ID}: {self.location}, ${self.price}>'

class House(db.Model):
    __tablename__ = 'House'
    
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'), primary_key=True)
    num_rooms = db.Column(db.Integer)
    square_footage = db.Column(db.Integer)
    
    # Relationship to Property
    property = db.relationship('Property', backref=db.backref('house', uselist=False))
    
    def __repr__(self):
        return f'<House {self.property_id}: {self.num_rooms} rooms, {self.square_footage} sq ft>'

class Apartment(db.Model):
    __tablename__ = 'Apartment'
    
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'), primary_key=True)
    num_rooms = db.Column(db.Integer)
    square_footage = db.Column(db.Integer)
    building_type = db.Column(db.String(100))
    
    # Relationship to Property
    property = db.relationship('Property', backref=db.backref('apartment', uselist=False))
    
    def __repr__(self):
        return f'<Apartment {self.property_id}: {self.num_rooms} rooms, {self.building_type}>'

class CommercialBuilding(db.Model):
    __tablename__ = 'Commercial_Building'
    
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'), primary_key=True)
    square_footage = db.Column(db.Integer)
    business_type = db.Column(db.String(100))
    
    # Relationship to Property
    property = db.relationship('Property', backref=db.backref('commercial_building', uselist=False))
    
    def __repr__(self):
        return f'<CommercialBuilding {self.property_id}: {self.business_type}>'

class VacationHome(db.Model):
    __tablename__ = 'Vacation_Home'
    
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'), primary_key=True)
    square_footage = db.Column(db.Integer)
    amenities = db.Column(db.Text)
    max_occupancy = db.Column(db.Integer)
    is_seasonal = db.Column(db.Boolean)
    
    # Relationship to Property
    property = db.relationship('Property', backref=db.backref('vacation_home', uselist=False))
    
    def __repr__(self):
        return f'<VacationHome {self.property_id}: {self.max_occupancy} occupancy>'

class Land(db.Model):
    __tablename__ = 'Land'
    
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'), primary_key=True)
    acreage = db.Column(db.Numeric)
    utilities = db.Column(db.Text)
    
    # Relationship to Property
    property = db.relationship('Property', backref=db.backref('land', uselist=False))
    
    def __repr__(self):
        return f'<Land {self.property_id}: {self.acreage} acres>'

class Booking(db.Model):
    __tablename__ = 'Booking'
    
    ID = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('User.ID'))
    property_id = db.Column(db.Integer, db.ForeignKey('Property.ID'))
    card_id = db.Column(db.Integer, db.ForeignKey('Credit_Card.ID'))
    booking_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_canceled = db.Column(db.Boolean)
    
    # Relationships
    renter = db.relationship('User', backref='bookings')
    credit_card = db.relationship('CreditCard', backref='bookings')
    
    def __repr__(self):
        return f'<Booking {self.ID}: Property {self.property_id}, {self.start_date} to {self.end_date}>'