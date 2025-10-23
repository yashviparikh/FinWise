from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:hinaldbms123@127.0.0.1:3306/investment'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    from .routes import routes_bp
    from .dashboard import dashboard_bp   # ✅ import here, after db is defined

    app.register_blueprint(routes_bp)
    app.register_blueprint(dashboard_bp)

    return app
