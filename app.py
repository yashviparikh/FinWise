from flask import Flask,render_template,jsonify
from dotenv import load_dotenv
import os
from dbmodel import db
load_dotenv()  # Load .env file

app=Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI']="mysql+pymysql://root:yashvi8569@localhost:3306/finwise"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def dashboard():
    print("hello")
    return render_template("index.html")

@app.route('/portfolio')
def portfolio():
    print("hello portfolio")
    return render_template("portfolio.html")

if __name__=="__main__":
    app.run(debug=True)