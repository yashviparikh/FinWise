import yfinance as yf

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "ltp": info['regularMarketPrice'],
        "change": info['regularMarketChange'],
        "percent_change": info['regularMarketChangePercent']
    }

data = get_stock_data("TATAGOLD.NS")
print(data)