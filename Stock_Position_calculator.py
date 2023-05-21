import argparse
import requests
from rich.table import Table
from rich.console import Console

class StockTrader:
    def __init__(self, ticker, risk_amount, api_key):
        self.ticker = ticker
        self.risk_amount = risk_amount
        self.api_key = api_key

    def get_recent_close_price(self):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.ticker}&apikey={self.api_key}'
        response = requests.get(url)
        data = response.json()
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return float(data['Global Quote']['05. price'])
        else:
            print(f"Could not fetch recent close price for {self.ticker}")
            return None

    def calculate_trade(self):
        close_price = self.get_recent_close_price()
        if close_price is not None:
            stop_loss = close_price * 0.98  # Set stop loss level 2% below recent close price
            shares_to_buy = self.risk_amount / (close_price - stop_loss)
            position_size = shares_to_buy * close_price
            return stop_loss, shares_to_buy, position_size, close_price
        else:
            return None, None, None

def main(ticker, risk_amount):
    api_key = 'LL6JIGZ7J1TZUXUW'
    trader = StockTrader(ticker, risk_amount, api_key)
    stop_loss, shares_to_buy, position_size, close_price = trader.calculate_trade()

    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Ticker")
    table.add_column("Risk Amount")
    table.add_column("Stop Loss")
    table.add_column("Shares to Buy")
    table.add_column("Position Size")
    table.add_column("Close Price")

    if stop_loss is not None and shares_to_buy is not None and position_size is not None:
        table.add_row(ticker, f"{str(risk_amount)}$", f"{stop_loss:.2f}$", f"{shares_to_buy:.2f}", f"{position_size:.2f}$", f"{close_price:.2f}")
    else:
        table.add_row(ticker, str(risk_amount), "Could not calculate", "Could not calculate", "Could not calculate")

    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="Ticker symbol for the stock")
    parser.add_argument("--risk_amount", type=float, help="Amount in dollars to risk per trade")
    args = parser.parse_args()

    main(args.ticker, args.risk_amount)
