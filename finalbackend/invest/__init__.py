from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Allowed frontend origins
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Configure CORS for the whole app and ensure preflight/credentials work
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
    )

    # Blueprints
    from .routes import routes_bp
    from .dashboard import dashboard_bp   # import here, after db is defined
    from .auth import auth_bp

    # Create database tables
    with app.app_context():
        db.create_all()

    # Also apply CORS rules at blueprint level for certainty (especially in some Flask versions)
    try:
        CORS(routes_bp, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)
        CORS(dashboard_bp, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)
        CORS(auth_bp, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)
    except Exception:
        # If Flask-CORS already initialized these, ignore
        pass

    app.register_blueprint(routes_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)

    @app.after_request
    def add_cors_headers(response):
        """Guarantee CORS headers on all responses, including errors.
        This complements flask-cors in cases where exceptions bypass its wrapper.
        """
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = ", ".join(filter(None, [response.headers.get("Vary"), "Origin"]))
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            # Keep header list minimal to avoid triggering unnecessary preflights
            # Include custom auth header used by the frontend
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Id")
        return response

    # Global exception handler: return JSON and ensure CORS headers are present
    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        # Log full traceback on the server console for debugging
        import traceback
        traceback.print_exc()

        # Build JSON response so frontend gets structured error info
        resp = jsonify({"error": str(e)})
        resp.status_code = 500

        # Ensure CORS headers are present even for exceptions
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            # Include custom auth header used by the frontend
            resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Id")

        return resp

    return app
