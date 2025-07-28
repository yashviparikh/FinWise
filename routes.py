from flask import app,Flask,render_template,jsonify,request
from portfolio import gettingfromdb, buy, sell, usercheck


def register_routes(app):
    @app.route('/')
    def dashboard():
        print("hello")
        return render_template("index.html")

    @app.route('/portfolio/<int:userid>',methods=['GET'])
    def getportfoliofromuserid(userid):
        try:
            data=gettingfromdb(userid)
            return jsonify(data)
        except Exception as e:
            return jsonify ({"error": str(e)}),500
        
    @app.route('/buy',methods=['POST'])
    def buystock():
        data=request.get_json()
        try:
            buy(userid=data['userid'],
                stockname=data['stockname'],
                qty=int(data['qty']),
                price=float(data['price']),
                companyname=data['companyname']
            )
            return jsonify({"message": "Buy successful"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/sell', methods=['POST'])
    def sell_stock():
        data = request.get_json()
        try:
            sell(
                userid=data['userid'],
                stockname=data['stockname'],
                qty=int(data['qty']),
                price=float(data['price']),
                companyname=data['companyname']
            )
            return jsonify({"message": "Sell successful"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/user/<int:userid>', methods=['GET'])
    def get_user(userid):
        try:
            user = usercheck(userid)
            return jsonify(user)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
