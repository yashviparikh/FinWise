# from app import app  
# from dbmodel import db

# with app.app_context():
#     db.drop_all()       
#     db.create_all()     
#     print("Database initialized successfully!")
from app import app  # or wherever you initialize the Flask app
from dbmodel import db, User, Portfolio, Transactionhistory, FIFOLot
from datetime import datetime

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create mock user
    user = User(name="Test User", money=5000.00)
    db.session.add(user)
    db.session.commit()

    # Add two portfolio entries (e.g., Reliance and TCS)
    portfolio1 = Portfolio(
        userid=user.userid,
        stockname="RELIANCE.NS",
        companyname="Reliance",
        totalquantity=5,
        averagebuyprice=2400.00,
        totalinvested=12000.00
    )
    portfolio2 = Portfolio(
        userid=user.userid,
        stockname="TCS.NS",
        companyname="TCS",
        totalquantity=3,
        averagebuyprice=3200.00,
        totalinvested=9600.00
    )
    db.session.add_all([portfolio1, portfolio2])
    db.session.commit()

    # Add transactions
    transaction1 = Transactionhistory(
        userid=user.userid,
        portfolioid=portfolio1.portfolioid,
        companyname="Reliance",
        stockname="RELIANCE.NS",
        quantity=5,
        price=2400.00,
        transactiontype="buy",
        timestamp=datetime.utcnow()
    )
    transaction2 = Transactionhistory(
        userid=user.userid,
        portfolioid=portfolio2.portfolioid,
        companyname="TCS",
        stockname="TCS.NS",
        quantity=3,
        price=3200.00,
        transactiontype="buy",
        timestamp=datetime.utcnow()
    )
    db.session.add_all([transaction1, transaction2])
    db.session.commit()

    # Optional: Add FIFO lots if using FIFO later
    fifolot1 = FIFOLot(
        userid=user.userid,
        portfolioid=portfolio1.portfolioid,
        companyname="Reliance",
        quantityremaining=5,
        pricepershare=2400.00,
        buydate=datetime.utcnow()
    )
    fifolot2 = FIFOLot(
        userid=user.userid,
        portfolioid=portfolio2.portfolioid,
        companyname="TCS",
        quantityremaining=3,
        pricepershare=3200.00,
        buydate=datetime.utcnow()
    )
    db.session.add_all([fifolot1, fifolot2])
    db.session.commit()

    print("✅ Mock data inserted successfully.")
