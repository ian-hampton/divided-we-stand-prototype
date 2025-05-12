from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app

app = create_app()