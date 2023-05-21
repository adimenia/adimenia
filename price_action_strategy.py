import argparse
import requests
import pandas as pd
from scipy.signal import argrelextrema
import numpy as np
from sklearn.linear_model import LinearRegression

class MarketData:
    def __init__(self, ticker, api_key):
        self.ticker = ticker
        self.api_key = api_key

    def is_valid_ticker(self):
        url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={self.ticker}&apikey={self.api_key}'
        response = requests.get(url)
        data = response.json()
        if 'bestMatches' in data and len(data['bestMatches']) > 0:
            for item in data['bestMatches']:
                if item['1. symbol'] == self.ticker:
                    return True
        return False

    def get_data(self, timeframe, from_date=None, to_date=None):

        try:
            function = 'TIME_SERIES_DAILY_ADJUSTED' if timeframe == '1d' else 'TIME_SERIES_WEEKLY_ADJUSTED'
            url = f'https://www.alphavantage.co/query?function={function}&symbol={self.ticker}&apikey={self.api_key}'
            response = requests.get(url)
            data = response.json()
            key = next(key for key in data if "Time Series" in key)
            df = pd.DataFrame(data[key]).T
            df.index = pd.to_datetime(df.index)
            df = df.apply(pd.to_numeric)
            if from_date:
                df = df[df.index >= from_date]
            if to_date:
                df = df[df.index <= to_date]
            return df
        except Exception as e:
            print(f"An error occurred: {e}")

    def find_support_resistance(self, df):
        # We use argrelextrema for this purpose
        df['min'] = df.iloc[argrelextrema(df['4. close'].values, np.less_equal)[0]]['4. close']
        df['max'] = df.iloc[argrelextrema(df['4. close'].values, np.greater_equal)[0]]['4. close']

        support = df['min'].dropna()
        resistance = df['max'].dropna()

        return support, resistance
    def bullish_momentum(self, data, period=4):
        data['Momentum'] = (data['4. close'] - data['4. close'].shift(period)) > 0
        return data[data['Momentum']]
    
    def is_uptrend(self, df):
        model = LinearRegression()
        y = df['4. close'].values.reshape(-1, 1)
        x = np.array(range(len(df))).reshape(-1, 1)
        model.fit(x, y)
        slope = model.coef_
        if slope > 0:
            return True
        else:
            return False


def main(args):
    api_key = 'LL6JIGZ7J1TZUXUW'

    market_data = MarketData(args.ticker, api_key)
    if market_data.is_valid_ticker():
        daily_data = market_data.get_data('1d', args.from_date, args.to_date)
        weekly_data = market_data.get_data('1w', args.from_date, args.to_date)
        if daily_data is not None:
            #support, resistance = market_data.find_support_resistance(daily_data)
            '''print("Daily Support levels: ")
            print(support)
            print("Daily Resistance levels: ")
            print(resistance)'''
            daily_bullish_momentum = market_data.bullish_momentum(daily_data)
            print("Bullish momentum on daily level:\n", daily_bullish_momentum)
            print(f"Is the stock in an uptrend on a Daily level? {market_data.is_uptrend(daily_data)}")      
        if weekly_data is not None:
            #support, resistance = market_data.find_support_resistance(weekly_data)
            '''print("Weekly Support levels: ")
            print(support)
            print("Weekly Resistance levels: ")
            print(resistance)'''
            weekly_bullish_momentum = market_data.bullish_momentum(weekly_data)
            print("Bullish momentum on weekly level:\n", weekly_bullish_momentum)
            print(f"Is the stock in an uptrend on a weekly level? {market_data.is_uptrend(weekly_data)}")
    else:
        print(f"The entered ticker '{args.ticker}' is invalid. Please enter a valid ticker symbol.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", help="Ticker symbol for the stock")
    parser.add_argument("--from_date", help="Start date for the data in the format YYYY-MM-DD", default=None)
    parser.add_argument("--to_date", help="End date for the data in the format YYYY-MM-DD", default=None)
    args = parser.parse_args()

    main(args)
