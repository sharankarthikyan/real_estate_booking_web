from flask import Flask, render_template
from config import Config
from datetime import datetime
import database

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize database
    database.init_app(app)
    
    # Register blueprints
    from routes import init_app as init_routes
    init_routes(app)
    
    # Add global template variables
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)