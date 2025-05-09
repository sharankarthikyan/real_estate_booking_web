from flask import Blueprint

user_bp = Blueprint('user', __name__, url_prefix='/users')
property_bp = Blueprint('property', __name__, url_prefix='/properties')

def init_app(app):
    # Import routes to register them with the blueprints
    from . import user_routes, property_routes
    
    # Register blueprints with the app
    app.register_blueprint(user_bp)
    app.register_blueprint(property_bp)