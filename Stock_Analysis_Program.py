import argparse
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rich.table import Table
from rich.console import Console
from scipy.signal import argrelextrema
import matplotlib.dates as mdates

api_key = '35be1029cedf3eb8adf1ad315ce9928b'
fibonacci_levels = {
        0.0: '0%',
        0.236: '23.6%',
        0.382: '38.2%',
        0.5: '50%',
        0.618: '61.8%',
        0.786: '78.6%',
        1.0: '100%'
    }

class TradingStrategy:
    def __init__(self, tickers, lookback_period=2, risk_reward_ratio=(2, 5), interval='1week', window_size=5):
        self.api_key = api_key
        self.tickers = tickers
        self.lookback_period = lookback_period
        self.risk_reward_ratio = risk_reward_ratio
        self.interval = interval
        self.window_size = window_size
        self.data = {}
        
    def calculate_fibonacci_retracement_levels(self, ticker):
        data = self.data[ticker].copy()
        high = data['high'].max()
        low = data['low'].min()

        retracement_levels = {}

        for level, ratio in self.fibonacci_levels.items():
            retracement = high - (ratio * (high - low))
            retracement_levels[level] = retracement

        return retracement_levels
        
    def fetch_data(self, interval='24hour'):  # Use a default value of '1hour' instead of '1week'
        end_date = datetime.today()
        start_date = end_date - timedelta(weeks=self.lookback_period * 52)
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        valid_intervals = ['1min', '5min', '10min', '15min', '30min', '1hour', '3hour', '6hour', '12hour', '24hour']
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval value. Valid values are {', '.join(valid_intervals)}")
        for ticker in self.tickers:
            url = f'http://api.marketstack.com/v1/eod?access_key={self.api_key}&symbols={ticker}&date_from={start_date}&date_to={end_date}&interval={interval}'
            response = requests.get(url)
            data = pd.DataFrame(response.json()['data'])
            data.set_index('date', inplace=True)
            self.data[ticker] = data
            
    def find_support_resistance(self, ticker):
        data = self.data[ticker]['close']
        
        # Find local minima and maxima as support and resistance levels
        local_minima = argrelextrema(data.values, np.less)
        local_maxima = argrelextrema(data.values, np.greater)
        
        support_levels = data.iloc[local_minima].to_dict()
        resistance_levels = data.iloc[local_maxima].to_dict()
        
        return support_levels, resistance_levels
    
    def find_moving_averages(self, ticker):
        data = self.data[ticker]['close']
        short_term_sma = data.rolling(window=50).mean()
        long_term_sma = data.rolling(window=150).mean()
        return short_term_sma, long_term_sma

    def find_momentum(self, ticker):
        data = self.data[ticker]['close']
        
        # Calculate the rate of change (momentum)
        rate_of_change = data.pct_change().rolling(window=self.window_size).mean()
        recent_momentum = rate_of_change[-1]
        
        # Check if the recent momentum is positive (bullish)
        bullish_momentum = recent_momentum > 0
        
        return bullish_momentum, recent_momentum

    def find_trend(self, ticker):
        data = self.data[ticker]['close']
        
        # Calculate short-term and long-term simple moving averages
        short_term_sma = data.rolling(window=20).mean()
        long_term_sma = data.rolling(window=50).mean()

        # Check if the short-term SMA is above the long-term SMA (uptrend)
        recent_short_term_sma = short_term_sma[-1]
        recent_long_term_sma = long_term_sma[-1]
        uptrend = recent_short_term_sma > recent_long_term_sma

        return uptrend, short_term_sma, long_term_sma

    def find_candlestick_pattern(self, ticker):
        data = self.data[ticker]
        
        # Calculate the body size and shadow size of each candle
        data['body'] = abs(data['close'] - data['open'])
        data['upper_shadow'] = data['high'] - data[['open', 'close']].max(axis=1)
        data['lower_shadow'] = data[['open', 'close']].min(axis=1) - data['low']
        
        # Check for a bullish engulfing pattern
        bullish_engulfing = (
            (data['open'] > data['close'].shift(1)) & 
            (data['close'] > data['open'].shift(1)) &
            (data['body'] > data['body'].shift(1))
        )
        
        # Check for a doji pattern
        doji = (
            (data['body'] / (data['high'] - data['low']) <= 0.1)
        )
        
        # Check for a shooting star pattern
        shooting_star = (
            (data['upper_shadow'] >= 2 * data['body']) &
            (data['lower_shadow'] <= data['body'])
        )
        
        # Check for a hanging man pattern
        hanging_man = (
            (data['upper_shadow'] <= data['body']) &
            (data['lower_shadow'] >= 2 * data['body'])
        )
        
        # Find the most recent trend change pattern
        recent_trend_change = (
            bullish_engulfing.iloc[-1] or
            doji.iloc[-1] or
            shooting_star.iloc[-1] or
            hanging_man.iloc[-1]
        )

        return recent_trend_change, {
            'bullish_engulfing': bullish_engulfing,
            'doji': doji,
            'shooting_star': shooting_star,
            'hanging_man': hanging_man
        }

    def find_fibonacci_area(self, ticker):
        data = self.data[ticker]['close']
        
        # Find the highest and lowest points of the price data
        highest_point = data.max()
        lowest_point = data.min()
        
        # Calculate the Fibonacci retracement levels
        fibonacci_ratio = 0.618
        retracement_level = lowest_point + (highest_point - lowest_point) * fibonacci_ratio

        return retracement_level

    def find_confluence_area(self, ticker, tolerance=0.01):
        retracement_level = self.find_fibonacci_area(ticker)
        support_levels, resistance_levels = self.find_support_resistance(ticker)
        uptrend, short_term_sma, long_term_sma = self.find_trend(ticker)
        recent_trend_change, trend_change_patterns = self.find_trend_change_patterns(ticker)

        # Check if the Fibonacci retracement level is near a key support, resistance level,
        # short-term SMA, long-term SMA, or a recent bullish trend change pattern
        confluence = False

        def is_near_level(price, level, tolerance):
            return abs(price - level) / price <= tolerance

        for level in list(support_levels.values()) + list(resistance_levels.values()):
            if is_near_level(retracement_level, level, tolerance):
                confluence = True
                break

        if not confluence:
            recent_short_term_sma = short_term_sma.iloc[-1]
            recent_long_term_sma = long_term_sma.iloc[-1]

            if (is_near_level(retracement_level, recent_short_term_sma, tolerance) or
                    is_near_level(retracement_level, recent_long_term_sma, tolerance)):
                confluence = True

        if not confluence and recent_trend_change:
            for pattern_name, pattern_data in trend_change_patterns.items():
                if pattern_data.iloc[-1]:
                    pattern_price = self.data.loc[pattern_data.index[-1], 'close']
                    if is_near_level(retracement_level, pattern_price, tolerance):
                        confluence = True
                        break

        return confluence, retracement_level

    def find_trend_change_patterns(self, ticker):
        data = self.data[ticker]['close']

        def is_extreme(price_data, comparator):
            return argrelextrema(np.array(price_data), comparator=comparator)

        local_maxima = is_extreme(data, np.greater)
        local_minima = is_extreme(data, np.less)

        def find_double_top_bottom(price_data, extrema_indices, pattern_type='double_top'):
            threshold = 0.05
            patterns = []

            for i in range(len(extrema_indices) - 1):
                idx1 = extrema_indices[i]
                idx2 = extrema_indices[i + 1]

                if (1 - threshold) * price_data[idx1] <= price_data[idx2] <= (1 + threshold) * price_data[idx1]:
                    if pattern_type == 'double_top':
                        if data[idx1] > data[idx1 - 1] and data[idx1] > data[idx1 + 1] and \
                                data[idx2] > data[idx2 - 1] and data[idx2] > data[idx2 + 1]:
                            patterns.append((idx1, idx2))
                    elif pattern_type == 'double_bottom':
                        if data[idx1] < data[idx1 - 1] and data[idx1] < data[idx1 + 1] and \
                                data[idx2] < data[idx2 - 1] and data[idx2] < data[idx2 + 1]:
                            patterns.append((idx1, idx2))

            return patterns

        double_tops = find_double_top_bottom(data, local_maxima, pattern_type='double_top')
        double_bottoms = find_double_top_bottom(data, local_minima, pattern_type='double_bottom')

        # Additional patterns such as Head and Shoulders and Inverse Head and Shoulders
        # can be implemented similarly using the local maxima and minima.
        # ...

        return {
            'double_tops': double_tops,
            'double_bottoms': double_bottoms,
            # ...
        }

    def analyze_ticker(self, ticker):
        # Call the analysis helper methods for the ticker
        self.find_support_resistance(ticker)
        self.find_moving_averages(ticker)
        self.find_momentum(ticker)
        self.find_trend(ticker)
        self.find_trend_change_patterns(ticker)
        self.find_fibonacci_area(ticker)
        self.find_confluence_area(ticker)
        self.generate_buy_signal(ticker)
        self.print_analysis(ticker)
        
    def generate_buy_signal(self, ticker):
        # Check if the stock is in an uptrend
        uptrend, short_term_sma, long_term_sma = self.find_trend(ticker)

        # Check if there is a recent bullish trend change pattern
        recent_trend_change, trend_change_patterns = self.find_trend_change_patterns(ticker)

        # Check if there is a confluence area near the current price
        confluence, retracement_level = self.find_confluence_area(ticker)

        # Check if the price is above the 150-day moving average
        data = self.data[ticker]
        price_above_ma = data['close'] > data['close'].rolling(window=150).mean()[-1]

        # Calculate the buy signal strength based on the conditions met
        buy_signal_strength = 0
        total_conditions = 4

        if uptrend:
            buy_signal_strength += 1
        if recent_trend_change:
            buy_signal_strength += 1
        if confluence:
            buy_signal_strength += 1
        if price_above_ma.any():
            buy_signal_strength += 1

        buy_signal_strength_percentage = (buy_signal_strength / total_conditions) * 100

        return buy_signal_strength_percentage

    def print_analysis(self, ticker):
        buy_signal_strength = self.generate_buy_signal(ticker)
        uptrend, short_term_sma, long_term_sma = self.find_trend(ticker)
        recent_trend_change, trend_change_patterns = self.find_trend_change_patterns(ticker)
        confluence, retracement_level = self.find_confluence_area(ticker)

        # Calculate the recommended price entry
        current_price = self.data[ticker]['close'].iloc[-1]
        recommended_price_entry = retracement_level

        # Calculate the best stop-loss based on a risk-reward ratio of 2:5
        risk_reward_ratio = 2 / 5
        stop_loss = current_price - (current_price - recommended_price_entry) * risk_reward_ratio

        # Print the analysis in a table format using Python rich
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ticker")
        table.add_column("Buy Signal Strength")
        table.add_column("Reasoning")
        table.add_column("Recommended Price Entry")
        table.add_column("Best Stop-Loss")

        reasoning = []
        if uptrend:
            reasoning.append("Uptrend")
        if recent_trend_change:
            reasoning.append("Trend Change Pattern")
        if confluence:
            reasoning.append("Confluence Area")

        table.add_row(
            ticker,
            f"{buy_signal_strength:.2f}%",
            ", ".join(reasoning),
            f"${recommended_price_entry:.2f}",
            f"${stop_loss:.2f}"
        )

        console.print(table)

    def plot_stock_graph(self, ticker, save_to_file=False):
        data = self.data[ticker].copy()
        short_term_sma = data['short_term_sma']
        long_term_sma = data['long_term_sma']
        support_levels, resistance_levels = self.find_support_resistance(ticker)
        retracement_levels = self.calculate_fibonacci_retracement_levels(ticker)
        

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(data.index, data['close'], label=f"{ticker} Close", linewidth=1.5)
        ax.plot(data.index, short_term_sma, label="Short Term SMA", linewidth=1, linestyle="--", color="orange")
        ax.plot(data.index, long_term_sma, label="Long Term SMA", linewidth=1, linestyle="--", color="blue")

        # Plot support and resistance levels
        for level in support_levels:
            ax.axhline(level, linestyle="--", linewidth=1, color="green", alpha=0.6)

        for level in resistance_levels:
            ax.axhline(level, linestyle="--", linewidth=1, color="red", alpha=0.6)

        # Plot Fibonacci retracement levels
        for level in retracement_levels.values():
            ax.axhline(level, linestyle="--", linewidth=1, color="purple", alpha=0.6)

        ax.set_title(f"{ticker} Stock Price")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{ticker}-{timestamp}.png"
            plt.savefig(filename)
            print(f"Stock graph saved as {filename}")
        else:
            plt.show()

    def run_strategy(self):
        self.fetch_data()
        
        for ticker in self.tickers:
            self.analyze_ticker(ticker)
            self.print_analysis(ticker)
            
            plot_graph = input(f"Do you want to plot the stock graph for {ticker}? (y/n): ")
            if plot_graph.lower() == 'y':
                self.plot_stock_graph(ticker, save_to_file=True)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tickers', help='Comma-separated list of tickers', required=True)
    parser.add_argument('-l', '--lookback', help='Lookback period in years (default: 2)', default=2, type=int)
    args = parser.parse_args()
    
    return args.tickers.split(','), args.lookback

if __name__ == '__main__':
    tickers, lookback_period = parse_arguments()
    strategy = TradingStrategy(tickers, lookback_period=lookback_period)
    strategy.run_strategy()