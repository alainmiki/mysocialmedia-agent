import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = SQLAlchemy()
celery = Celery(__name__,
                broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
                backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Update Celery configuration
    celery.conf.update(app.config)

    # --- Fix for NoAppException ---
    # Create a custom Task class that wraps tasks in an application context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    # ------------------------------

    # Register blueprints
    from src.posts.routes import posts_bp
    app.register_blueprint(posts_bp)

    with app.app_context():
        db.create_all()  # Create database tables

    return app
