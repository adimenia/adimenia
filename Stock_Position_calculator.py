import argparse
import requests
from rich.table import Table
from rich.console import Console
import datetime
from alpaca_trade_api.rest import REST, TimeFrame
import pandas_market_calendars as mcal
import pandas as pd
import json
import os

class StockTrader:
    def __init__(self, ticker, risk_amount, api_key):
        self.ticker = ticker
        self.risk_amount = risk_amount
        self.api_key = api_key
        self.total_account_size = 2000
        self.total_account_risk = 0.02
        #self.api = REST(api_key, secret_key)
    
    def load_config(self, config_file_path='config.json'):
        if not os.path.isfile(config_file_path):
            print(f"No config file found at {config_file_path}. Using command line arguments or defaults.")
            return
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        self.api_key = config.get('api_key', self.api_key)
        self.total_account_size = config.get('total_account_size', self.total_account_size)
        self.total_account_risk = config.get('total_account_risk', self.total_account_risk)
        self.risk_amount = config.get('risk_amount', self.risk_amount)

    def is_trading_day(self, date):
        nyse = mcal.get_calendar('NYSE')
        trading_days = nyse.valid_days(start_date=date, end_date=date)
        return not trading_days.empty


    def get_recent_close_price(self):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.ticker}&apikey={self.api_key}'
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return float(data['Global Quote']['05. price'])
        else:
            raise Exception(f"Could not fetch recent close price for {self.ticker}")
        
    def get_close_price_on_date(self, date):
        if not self.is_trading_day(date):
            raise Exception(f"No trading data available for {self.ticker} on {date}")
        
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={self.ticker}&apikey={self.api_key}'
        response = requests.get(url, timeout=10)
        data = response.json()

        if 'Time Series (Daily)' in data and date in data['Time Series (Daily)']:
            return float(data['Time Series (Daily)'][date]['4. close'])
        else:
             raise Exception(f"Could not fetch recent close price for {self.ticker}")
        
    def get_atr(self):
        url = f'https://www.alphavantage.co/query?function=ATR&symbol={self.ticker}&interval=daily&time_period=14&apikey={self.api_key}'
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'Technical Analysis: ATR' in data:
            # get the most recent ATR value
            recent_date = list(data['Technical Analysis: ATR'].keys())[0]
            return float(data['Technical Analysis: ATR'][recent_date]['ATR'])
        else:
            print(f"Could not fetch ATR for {self.ticker}")
            return None

    def calculate_trade(self, start_date=None):
        if start_date is not None:
            close_price = self.get_close_price_on_date(start_date)
        else:
            close_price = self.get_recent_close_price()

        atr = self.get_atr()
        if close_price is not None and atr is not None:
            stop_loss = close_price - atr  # Set stop loss level to entry price minus ATR
            shares_to_buy = self.risk_amount / (close_price - stop_loss)
            position_size = shares_to_buy * close_price
            return stop_loss, shares_to_buy, position_size, close_price
        else:
            return None, None, None, None

    def back_test(self, start_date):
        # Get NYSE calendar
        nyse = mcal.get_calendar('NYSE')
    
        # Calculate yesterday's date
        yesterday = pd.Timestamp.today() - pd.DateOffset(days=1)
    
        # Get all valid trading days from start_date to yesterday
        valid_days = nyse.valid_days(start_date=start_date, end_date=yesterday)

        # If there are no valid trading days in the range, handle this case as appropriate
        if valid_days.empty:
            print("No valid trading days in the specified range.")
            return None, None, None, None, None, None, None, None, None, "Backtest Failed"
        
        # Take the last valid trading day as end_date
        end_date = valid_days.max()

        # Convert it to string format
        end_date_str = end_date.strftime('%Y-%m-%d')

        print(f"Backtesting from {start_date} to {end_date_str}")

        # Calculate trade at the start date
        stop_loss, shares_to_buy, position_size, entry_price = self.calculate_trade(start_date)

        # Fetch the close price at the end of the period
        final_close_price = self.get_close_price_on_date(end_date_str)

        # Ensure that both entry_price and final_close_price are not None
        if entry_price is None or final_close_price is None:
            print("Backtest could not be performed due to missing price data.")
            return None, None, None, None, None, None, None, None, None, "Backtest Failed"

        # Calculate profit if we exit the trade at the final close price
        profit = (final_close_price - entry_price) * shares_to_buy
        profit_percent = (final_close_price - entry_price) / entry_price * 100

        # Determine if the trade was successful
        trade_outcome = "Winning trade" if profit > 0 else "Losing trade"
        return start_date, entry_price, self.risk_amount, stop_loss, shares_to_buy, position_size, final_close_price, profit_percent, profit, trade_outcome, end_date_str


def main(ticker, risk_amount, start_date=None,  config_file_path='config.json'):
    api_key = 'LL6JIGZ7J1TZUXUW'
    #secret_key = 'PKAA7525K2KNBQZXFW97'
    trader = StockTrader(ticker, risk_amount, api_key)
    trader.load_config(config_file_path)
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")

    if start_date:
        start_date, entry_price, risk_amount, stop_loss, shares_to_buy, position_size, final_close_price, profit_percent, profit, trade_outcome, end_date = trader.back_test(start_date)

        table.add_column("Start Date")
        table.add_column("Entry Price")
        table.add_column("Risk Amount")
        table.add_column("Stop Loss")
        table.add_column("Shares to Buy")
        table.add_column("Position Size")
        table.add_column("Close Price")
        table.add_column("Profit (%)")
        table.add_column("Profit ($)")
        table.add_column("Trade Outcome")
        table.add_column("End Date")

        table.add_row(start_date, f"{entry_price:.2f}", f"{risk_amount}$", f"{stop_loss:.2f}$", f"{shares_to_buy:.2f}", f"{position_size:.2f}$", f"{final_close_price:.2f}$", f"{profit_percent:.2f}%", f"{profit:.2f}$", trade_outcome, end_date)
    else:
        stop_loss, shares_to_buy, position_size, close_price = trader.calculate_trade()
        
        table.add_column("Ticker")
        table.add_column("Entry Price")
        table.add_column("Risk Amount")
        table.add_column("Stop Loss")
        table.add_column("Shares to Buy")
        table.add_column("Position Size")
        table.add_column("Close Price")

        if stop_loss is not None and shares_to_buy is not None and position_size is not None:
            table.add_row(ticker, f"{close_price:.2f}$", f"{str(risk_amount)}$", f"{stop_loss:.2f}$", f"{shares_to_buy:.2f}", f"{position_size:.2f}$", f"{close_price:.2f}")
        else:
            table.add_row(ticker, str(risk_amount), "Could not calculate", "Could not calculate", "Could not calculate")

    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="Ticker symbol for the stock", required=True)
    parser.add_argument("--risk_amount", type=float, help="Amount in dollars to risk per trade", required=True)
    parser.add_argument("--start_date", type=str, help="Date to start back test (YYYY-MM-DD format)")
    parser.add_argument("--config_file_path", type=str, help="Path to the config file", default='config.json')
    args = parser.parse_args()

    main(args.ticker, args.risk_amount, args.start_date, args.config_file_path)

