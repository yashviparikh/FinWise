from invest import create_app
import os

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    use_reloader = os.getenv("FLASK_USE_RELOADER", "0") == "1"
    app.run(debug=debug_mode, use_reloader=use_reloader)
