from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'User'
    
    ID = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    name = db.Column(db.String(255))
    is_agent = db.Column(db.Boolean)
    
    def __repr__(self):
        return f'<User {self.ID}: {self.email}>'

class Agent(db.Model):
    __tablename__ = 'Agent'
    
    user_id = db.Column(db.Integer, db.ForeignKey('User.ID'), primary_key=True)
    job_title = db.Column(db.String(255))
    real_estate_agency = db.Column(db.String(255))
    contact_info = db.Column(db.Text)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('agent_profile', uselist=False))
    
    def __repr__(self):
        return f'<Agent {self.user_id}: {self.real_estate_agency}>'

class ProspectiveRenter(db.Model):
    __tablename__ = 'Prospective_Renters'
    
    user_id = db.Column(db.Integer, db.ForeignKey('User.ID'), primary_key=True)
    desired_move_in_date = db.Column(db.Date)
    preferred_location = db.Column(db.String(255))
    budget = db.Column(db.Numeric)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('renter_profile', uselist=False))
    
    def __repr__(self):
        return f'<ProspectiveRenter {self.user_id}: {self.preferred_location}>'

class Address(db.Model):
    __tablename__ = 'Address'
    
    ID = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.ID'))
    street = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(100))
    
    # Relationship to User
    user = db.relationship('User', backref='addresses')
    
    def __repr__(self):
        return f'<Address {self.ID}: {self.street}, {self.city}>'

class RewardProgram(db.Model):
    __tablename__ = 'Reward_Program'
    
    renter_id = db.Column(db.Integer, db.ForeignKey('User.ID'), primary_key=True)
    reward_points = db.Column(db.Integer)
    
    # Relationship to User
    renter = db.relationship('User', backref=db.backref('reward_program', uselist=False))
    
    def __repr__(self):
        return f'<RewardProgram {self.renter_id}: {self.reward_points} points>'

class CreditCard(db.Model):
    __tablename__ = 'Credit_Card'
    
    ID = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.ID'))
    card_number = db.Column(db.String(20))
    expiration_date = db.Column(db.Date)
    payment_address_id = db.Column(db.Integer, db.ForeignKey('Address.ID'))
    
    # Relationships
    user = db.relationship('User', backref='credit_cards')
    payment_address = db.relationship('Address')
    
    def __repr__(self):
        return f'<CreditCard {self.ID}: ending in {self.card_number[-4:]}>'