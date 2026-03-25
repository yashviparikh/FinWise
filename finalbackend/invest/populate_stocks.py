import csv
import os
from invest import create_app, db
from invest.models import Stock


def main():
    """Populate the Stock table from stock_list.csv if symbols don't already exist."""
    app = create_app()
    csv_path = os.path.join(os.path.dirname(__file__), 'stock_list.csv')

    with app.app_context():
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            added = 0
            for row in reader:
                symbol = row['SYMBOL'].strip()
                name = row['NAME OF COMPANY'].strip()

                if not Stock.query.filter_by(stock_symbol=symbol).first():
                    new_stock = Stock(
                        stock_symbol=symbol,
                        stock_name=name,
                    )
                    db.session.add(new_stock)
                    added += 1

            db.session.commit()
        print(f"Stock data inserted successfully. Added {added} new symbols.")


if __name__ == "__main__":
    main()


