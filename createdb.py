import csv
from invest.models import Person,Stock,Watchlist
from invest import db,app

with app.app_context():
    with open('stock_list.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            symbol = row['SYMBOL'].strip()
            name = row['NAME OF COMPANY'].strip()

            if not Stock.query.filter_by(stock_symbol=symbol).first():
                new_stock = Stock(
                    stock_symbol=symbol,
                    stock_name=name,
                )
                db.session.add(new_stock)

        db.session.commit()
    print("Stock data inserted successfully.")


