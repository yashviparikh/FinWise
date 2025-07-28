from flask import Flask
from dotenv import load_dotenv
import os
from dbmodel import db
from flask_cors import CORS
load_dotenv()  
from extensions import db
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:yashvi8569@localhost:3306/finwise"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    register_routes(app)
    CORS(app)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
