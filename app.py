from flask import Flask,render_template,jsonify
import portfolio
app=Flask(__name__)

@app.route('/')
def dashboard():
    return render_template("dashboard.html")

@app.route('/portfolio')
def portfolio():
    return render_template("portfolio.html")
if __name__=="main":
    app.run(debug=True)