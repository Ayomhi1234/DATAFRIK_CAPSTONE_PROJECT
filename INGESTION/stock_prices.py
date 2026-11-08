
import yfinance as yf
import pandas as pd

# Stocks to track
stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'NFLX']


def fetch_stock_prices():

    all_data = []

    for ticker in stocks:
        print(f"Fetching data for {ticker}")

        stock = yf.Ticker(ticker)

        data = stock.history(
            period="1y",
            interval="1d"
        )

        if data.empty:
            print(f"No data found for {ticker}")
            continue

        data = data.reset_index()
        data["ticker"] = ticker

        all_data.append(data)

    if not all_data:
        print("No stock data was retrieved.")
        return None

    # Concatenate all dataframes
    stock_prices = pd.concat(all_data, ignore_index=True)

    # Display preview and summary
    print("\nStock Data Summary")
    stock_prices.info()

    print(stock_prices.head())

    print("\nTotal records:", len(stock_prices))

    print("\nRecords per Stock:")
    print(stock_prices['ticker'].value_counts())

        # Check the data types of each column
    print("\nData Types:")
    print(stock_prices.dtypes)

# Check for missing values
    print("\nMissing Values:")
    print(stock_prices.isnull().sum())

# Check for duplicate date and ticker combinations
    print("\nDuplicate Records:")
    print(stock_prices.duplicated(subset=["Date", "ticker"]).sum())

# Display the total number of records
    print("\nTotal Records:", len(stock_prices))
    # Save stock prices to CSV
   # stock_prices.to_csv("stock_prices.csv", index=False)

    #print("\nStock prices saved to 'stock_prices.csv'")

    return stock_prices


# Execute function
if __name__ == "__main__":
    stock_prices = fetch_stock_prices()
