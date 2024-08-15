from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load configuration settings
    # app.config.from_object('config.Config')
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app

app = create_app()