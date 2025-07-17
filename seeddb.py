
from app import app  
from dbmodel import db

with app.app_context():
    db.drop_all()       
    db.create_all()     
    print("Database initialized successfully!")
