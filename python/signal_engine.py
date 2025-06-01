#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2025 Immaginet Srl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import time
import json
import shutil
import logging
import argparse
import datetime
import pandas as pd
import numpy as np
import requests
import schedule
import pyarrow  # For pandas optimization
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Optional DeepSeek integration
try:
    from deepseek_utils import news_bias
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("signal_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("signal_engine")

# Constants
SYMBOLS = ["XAUUSD", "XAGUSD", "WTICOUSD", "BCOUSD", "NATGASUSD", "CORNUSD", "SOYBNUSD", "WHEATUSD"]
MT4_FILES_PATH = os.path.expanduser("~/AppData/Roaming/MetaTrader 4/MQL4/Files/OpenMT4TradingBot")
DATA_PATH = "../data"
COT_URL = "https://www.cftc.gov/dea/newcot/deacot.txt"  # CFTC Legacy COT report
UPDATE_INTERVAL_MINUTES = 1


class SignalEngine:
    """Main signal calculation engine for the OpenMT4TradingBot."""
    
    def __init__(self, mt4_path: str = None, data_path: str = None, use_deepseek: bool = False):
        """
        Initialize the signal engine.
        
        Args:
            mt4_path: Path to MT4 Files directory
            data_path: Path to data directory
            use_deepseek: Whether to use DeepSeek for news sentiment analysis
        """
        self.mt4_path = mt4_path or MT4_FILES_PATH
        self.data_path = data_path or DATA_PATH
        self.use_deepseek = use_deepseek and DEEPSEEK_AVAILABLE
        
        # Ensure directories exist
        os.makedirs(self.mt4_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
        
        # Load seasonal data
        self.seasonal_data = self.load_seasonal_data()
        
        # Load COT data (create if not exists)
        self.cot_data = self.load_cot_data()
        
        # Initialize empty signals dictionary
        self.signals = {}
        
        logger.info(f"Signal Engine initialized with MT4 path: {self.mt4_path}")
        logger.info(f"DeepSeek integration: {'Enabled' if self.use_deepseek else 'Disabled'}")

    def load_seasonal_data(self) -> Dict:
        """Load seasonal data from JSON file."""
        season_file = os.path.join(self.data_path, "season.json")
        
        if not os.path.exists(season_file):
            # Create default seasonal data if not exists
            default_data = {
                "XAUUSD": {"bull": [1, 2, 8, 9], "bear": [3, 6, 10]},
                "XAGUSD": {"bull": [1, 2, 7], "bear": [3, 5, 9, 10]},
                "WTICOUSD": {"bull": [1, 2, 3, 7, 8], "bear": [9, 10, 11]},
                "BCOUSD": {"bull": [1, 2, 3, 7, 8], "bear": [9, 10, 11]},
                "NATGASUSD": {"bull": [1, 2, 7, 12], "bear": [3, 4, 8, 9]},
                "CORNUSD": {"bull": [3, 4, 6], "bear": [9, 10, 11]},
                "SOYBNUSD": {"bull": [2, 3, 6, 7], "bear": [8, 9, 10]},
                "WHEATUSD": {"bull": [4, 5, 6], "bear": [1, 2, 9]}
            }
            
            with open(season_file, 'w') as f:
                json.dump(default_data, f, indent=2)
            
            logger.info(f"Created default seasonal data at {season_file}")
            return default_data
        
        try:
            with open(season_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded seasonal data from {season_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading seasonal data: {e}")
            return {}

    def load_cot_data(self) -> pd.DataFrame:
        """Load COT data from CSV file, update if needed."""
        cot_file = os.path.join(self.data_path, "cot.csv")
        
        # Check if COT data needs update (Friday or file doesn't exist)
        today = datetime.datetime.now()
        is_friday = today.weekday() == 4
        
        if not os.path.exists(cot_file) or is_friday:
            # Update COT data
            self.update_cot()
        
        try:
            df = pd.read_csv(cot_file, parse_dates=['Date'])
            logger.info(f"Loaded COT data from {cot_file}, {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading COT data: {e}")
            # Create empty dataframe with required columns
            columns = ['Date', 'Symbol', 'Commercial_Net', 'Commercial_Net_Normalized']
            return pd.DataFrame(columns=columns)

    def update_cot(self) -> bool:
        """
        Download and update the COT report data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        cot_file = os.path.join(self.data_path, "cot.csv")
        temp_file = os.path.join(self.data_path, "cot_temp.txt")
        
        try:
            # Download the latest COT report
            response = requests.get(COT_URL, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to download COT data: HTTP {response.status_code}")
                return False
            
            # Save the raw data
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Process the COT data - this is a simplified version
            # In reality, you'd need more sophisticated parsing for the CFTC format
            # The example below creates a synthetic dataset for demonstration
            
            # Mapping for symbols between MT4 and COT report
            symbol_mapping = {
                "GOLD": "XAUUSD",
                "SILVER": "XAGUSD",
                "CRUDE OIL, LIGHT SWEET": "WTICOUSD",
                "CRUDE OIL, BRENT": "BCOUSD",
                "NATURAL GAS": "NATGASUSD",
                "CORN": "CORNUSD",
                "SOYBEANS": "SOYBNUSD",
                "WHEAT": "WHEATUSD"
            }
            
            # Create a historical dataset (3 years of weekly data)
            today = datetime.datetime.now()
            weeks = 156  # 3 years
            
            dates = [today - datetime.timedelta(weeks=i) for i in range(weeks)]
            dates.reverse()  # Oldest first
            
            data = []
            for symbol_cot, symbol_mt4 in symbol_mapping.items():
                # Generate synthetic Commercial_Net positions with some randomness
                base_value = np.random.normal(0, 1)
                for i, date in enumerate(dates):
                    # Create time series with trend, seasonality and noise
                    t = i / len(dates)
                    trend = 20 * (t - 0.5)  # -10 to +10 over time
                    seasonality = 15 * np.sin(i/12 * 2 * np.pi)  # Annual cycle
                    noise = np.random.normal(0, 5)
                    
                    commercial_net = base_value + trend + seasonality + noise
                    
                    data.append({
                        'Date': date.strftime('%Y-%m-%d'),
                        'COT_Symbol': symbol_cot,
                        'Symbol': symbol_mt4,
                        'Commercial_Net': commercial_net
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Calculate normalized values (z-score over 3 years)
            for symbol in symbol_mapping.values():
                symbol_data = df[df['Symbol'] == symbol]
                mean = symbol_data['Commercial_Net'].mean()
                std = symbol_data['Commercial_Net'].std()
                
                if std > 0:  # Avoid division by zero
                    df.loc[df['Symbol'] == symbol, 'Commercial_Net_Normalized'] = (
                        (df.loc[df['Symbol'] == symbol, 'Commercial_Net'] - mean) / std
                    )
                else:
                    df.loc[df['Symbol'] == symbol, 'Commercial_Net_Normalized'] = 0
            
            # Save to CSV
            df.to_csv(cot_file, index=False)
            logger.info(f"Updated COT data saved to {cot_file}")
            
            # Update the cached data
            self.cot_data = df
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating COT data: {e}")
            return False

    def load_ohlc_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load OHLC data for a symbol from CSV file."""
        try:
            file_path = os.path.join(self.mt4_path, f"OHLC_{symbol}.csv")
            if not os.path.exists(file_path):
                logger.warning(f"OHLC file not found for {symbol}: {file_path}")
                return None
                
            df = pd.read_csv(file_path, parse_dates=['DateTime'])
            df.sort_values('DateTime', inplace=True)
            logger.debug(f"Loaded OHLC data for {symbol}, {len(df)} bars")
            return df
        except Exception as e:
            logger.error(f"Error loading OHLC data for {symbol}: {e}")
            return None

    def calculate_donchian_breakout(self, ohlc_df: pd.DataFrame, period: int = 40) -> Tuple[bool, bool]:
        """
        Calculate Donchian channel breakout.
        
        Args:
            ohlc_df: DataFrame with OHLC data
            period: Donchian channel period
            
        Returns:
            Tuple of (bullish_breakout, bearish_breakout)
        """
        if len(ohlc_df) < period + 1:
            return False, False
            
        # Get the last period + 1 bars
        df = ohlc_df.tail(period + 1).copy()
        
        # Calculate Donchian channel
        df['highest_high'] = df['High'].rolling(window=period).max().shift(1)
        df['lowest_low'] = df['Low'].rolling(window=period).min().shift(1)
        
        # Get last values
        last_close = df['Close'].iloc[-1]
        last_high = df['highest_high'].iloc[-1]
        last_low = df['lowest_low'].iloc[-1]
        
        # Check for breakout
        bullish_breakout = last_close >= last_high
        bearish_breakout = last_close <= last_low
        
        return bullish_breakout, bearish_breakout

    def check_cot_filter(self, symbol: str, direction: str) -> bool:
        """
        Check if the COT filter allows the trade.
        
        Args:
            symbol: Trading symbol
            direction: Trade direction ('BUY' or 'SELL')
            
        Returns:
            bool: True if trade is allowed, False otherwise
        """
        if self.cot_data.empty:
            logger.warning("COT data is empty, filter disabled")
            return True
            
        # Get the latest COT data for this symbol
        latest_cot = self.cot_data[self.cot_data['Symbol'] == symbol].tail(1)
        
        if latest_cot.empty:
            logger.warning(f"No COT data for {symbol}, filter disabled")
            return True
            
        # Get the normalized Commercial_Net position
        normalized_pos = latest_cot['Commercial_Net_Normalized'].iloc[0]
        
        # Apply COT filter rule
        if direction == 'BUY':
            # Long only if Commercial net position <= -1 std dev
            return normalized_pos <= -1
        else:  # 'SELL'
            # Short only if Commercial net position >= +1 std dev
            return normalized_pos >= 1

    def check_seasonal_filter(self, symbol: str, direction: str) -> float:
        """
        Check seasonal filter and return size multiplier.
        
        Args:
            symbol: Trading symbol
            direction: Trade direction ('BUY' or 'SELL')
            
        Returns:
            float: Size multiplier (1.0 = normal, 0.5 = reduced)
        """
        if symbol not in self.seasonal_data:
            logger.warning(f"No seasonal data for {symbol}, using normal sizing")
            return 1.0
            
        # Get current month (1-12)
        current_month = datetime.datetime.now().month
        
        # Get seasonal bias for this symbol
        symbol_seasons = self.seasonal_data[symbol]
        
        # Determine if current month is bullish or bearish
        is_bull_month = current_month in symbol_seasons.get('bull', [])
        is_bear_month = current_month in symbol_seasons.get('bear', [])
        
        # If trade direction matches seasonal bias, use normal sizing
        if (direction == 'BUY' and is_bull_month) or (direction == 'SELL' and is_bear_month):
            return 1.0
        # If trade direction opposite to seasonal bias, reduce size
        elif (direction == 'BUY' and is_bear_month) or (direction == 'SELL' and is_bull_month):
            return 0.5
        
        # If month is neither bullish nor bearish, use normal sizing
        return 1.0

    def calculate_atr(self, ohlc_df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Average True Range (ATR)."""
        if len(ohlc_df) < period:
            return 0.0
            
        df = ohlc_df.copy()
        
        # Calculate True Range
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df['Close'].shift(1))
        df['low_close'] = abs(df['Low'] - df['Close'].shift(1))
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # Calculate ATR
        atr = df['tr'].tail(period).mean()
        return atr

    def calculate_signals(self) -> Dict:
        """
        Calculate trading signals for all symbols.
        
        Returns:
            Dict: Dictionary of signals by symbol
        """
        signals = {}
        
        for symbol in SYMBOLS:
            # Load OHLC data
            ohlc_df = self.load_ohlc_data(symbol)
            if ohlc_df is None or len(ohlc_df) < 41:  # Need at least 41 bars
                continue
                
            # Calculate Donchian breakout
            bullish, bearish = self.calculate_donchian_breakout(ohlc_df)
            
            # If no breakout, skip to next symbol
            if not bullish and not bearish:
                continue
                
            # Determine direction
            direction = 'BUY' if bullish else 'SELL'
            
            # Check COT filter
            cot_allowed = self.check_cot_filter(symbol, direction)
            if not cot_allowed:
                logger.info(f"COT filter rejected {direction} signal for {symbol}")
                continue
                
            # Check seasonal filter for size adjustment
            size_multiplier = self.check_seasonal_filter(symbol, direction)
            
            # Apply DeepSeek news sentiment if available
            if self.use_deepseek:
                try:
                    from deepseek_utils import news_bias
                    bias, confidence = news_bias(symbol, [])  # TODO: Implement news headlines collection
                    
                    # If confidence is high and bias contradicts signal, reduce size or skip
                    if confidence > 0.7:
                        if (direction == 'BUY' and bias == 'bearish') or (direction == 'SELL' and bias == 'bullish'):
                            if confidence > 0.9:
                                logger.info(f"DeepSeek high confidence contrary bias for {symbol}, skipping signal")
                                continue
                            else:
                                logger.info(f"DeepSeek contrary bias for {symbol}, reducing size further")
                                size_multiplier *= 0.5
                except Exception as e:
                    logger.error(f"Error applying DeepSeek sentiment: {e}")
            
            # Calculate ATR for stops and targets
            atr = self.calculate_atr(ohlc_df)
            
            # Get current price
            current_price = ohlc_df['Close'].iloc[-1]
            
            # Calculate stop loss and take profit
            if direction == 'BUY':
                stop_loss = current_price - (1.5 * atr)
                take_profit = current_price + (3.0 * atr)
            else:  # SELL
                stop_loss = current_price + (1.5 * atr)
                take_profit = current_price - (3.0 * atr)
                
            # Calculate lot size (placeholder - would be calculated based on account equity in MT4)
            lot_size = 0.1 * size_multiplier
            
            # Create signal
            signals[symbol] = {
                'symbol': symbol,
                'direction': direction,
                'entry': current_price,
                'sl': stop_loss,
                'tp': take_profit,
                'lot': lot_size,
                'timestamp': int(time.time())
            }
            
            logger.info(f"Generated {direction} signal for {symbol} at {current_price}")
            
        return signals

    def export_signal(self, signal: Dict) -> bool:
        """
        Export a signal to JSON file for MT4.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not signal:
            return False
            
        signal_file = os.path.join(self.mt4_path, "signal.json")
        temp_file = os.path.join(self.mt4_path, "signal.tmp")
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w') as f:
                json.dump(signal, f, indent=2)
                
            # Replace the actual file
            shutil.move(temp_file, signal_file)
            
            logger.info(f"Signal exported to {signal_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting signal: {e}")
            return False

    def process_all_symbols(self) -> None:
        """Calculate and export signals for all symbols."""
        signals = self.calculate_signals()
        
        # Export each signal
        for symbol, signal in signals.items():
            self.export_signal(signal)
            # Sleep briefly between signals to avoid file conflicts
            time.sleep(1)

    def backtest(self) -> None:
        """
        Simple backtest function to validate the strategy.
        This is a minimalist implementation for quick testing.
        """
        results = {}
        
        for symbol in SYMBOLS:
            # Load OHLC data
            ohlc_df = self.load_ohlc_data(symbol)
            if ohlc_df is None or len(ohlc_df) < 100:  # Need enough history
                continue
                
            # Initialize variables
            equity = 10000.0
            position = None
            trades = []
            
            # Loop through each bar (skip the first 40 for lookback)
            for i in range(40, len(ohlc_df) - 1):
                # Create a dataframe with data up to current bar
                current_df = ohlc_df.iloc[:i+1].copy()
                
                # Check if we have an open position
                if position:
                    # Check if stop loss or take profit hit
                    current_bar = current_df.iloc[-1]
                    next_bar = ohlc_df.iloc[i+1]
                    
                    if position['direction'] == 'BUY':
                        # Check if stop loss hit
                        if next_bar['Low'] <= position['sl']:
                            profit = position['sl'] - position['entry']
                            equity += profit * position['size']
                            trades.append({**position, 'exit_price': position['sl'], 'profit': profit})
                            position = None
                        # Check if take profit hit
                        elif next_bar['High'] >= position['tp']:
                            profit = position['tp'] - position['entry']
                            equity += profit * position['size']
                            trades.append({**position, 'exit_price': position['tp'], 'profit': profit})
                            position = None
                    else:  # SELL
                        # Check if stop loss hit
                        if next_bar['High'] >= position['sl']:
                            profit = position['entry'] - position['sl']
                            equity += profit * position['size']
                            trades.append({**position, 'exit_price': position['sl'], 'profit': profit})
                            position = None
                        # Check if take profit hit
                        elif next_bar['Low'] <= position['tp']:
                            profit = position['entry'] - position['tp']
                            equity += profit * position['size']
                            trades.append({**position, 'exit_price': position['tp'], 'profit': profit})
                            position = None
                
                # If no position, check for new signal
                if not position:
                    bullish, bearish = self.calculate_donchian_breakout(current_df)
                    
                    if bullish or bearish:
                        direction = 'BUY' if bullish else 'SELL'
                        
                        # Check COT filter (simplified for backtest)
                        cot_allowed = True  # Simplified
                        
                        # Check seasonal filter
                        trade_date = current_df.iloc[-1]['DateTime']
                        month = trade_date.month
                        size_multiplier = 1.0
                        
                        if symbol in self.seasonal_data:
                            if direction == 'BUY':
                                if month in self.seasonal_data[symbol].get('bear', []):
                                    size_multiplier = 0.5
                            else:  # SELL
                                if month in self.seasonal_data[symbol].get('bull', []):
                                    size_multiplier = 0.5
                        
                        # If COT allows, enter trade
                        if cot_allowed:
                            atr = self.calculate_atr(current_df)
                            entry = current_df['Close'].iloc[-1]
                            
                            if direction == 'BUY':
                                sl = entry - (1.5 * atr)
                                tp = entry + (3.0 * atr)
                            else:  # SELL
                                sl = entry + (1.5 * atr)
                                tp = entry - (3.0 * atr)
                                
                            # Risk 1% of equity per trade
                            risk = equity * 0.01
                            size = (risk / (abs(entry - sl))) * size_multiplier
                            
                            position = {
                                'symbol': symbol,
                                'direction': direction,
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'size': size,
                                'date': trade_date
                            }
            
            # Calculate statistics
            if trades:
                wins = sum(1 for t in trades if t['profit'] > 0)
                losses = len(trades) - wins
                win_rate = wins / len(trades) if trades else 0
                
                avg_win = np.mean([t['profit'] for t in trades if t['profit'] > 0]) if wins else 0
                avg_loss = np.mean([t['profit'] for t in trades if t['profit'] <= 0]) if losses else 0
                
                profit_factor = abs(sum(t['profit'] for t in trades if t['profit'] > 0) / 
                                 sum(t['profit'] for t in trades if t['profit'] < 0)) if losses else float('inf')
                
                results[symbol] = {
                    'trades': len(trades),
                    'win_rate': win_rate,
                    'profit_factor': profit_factor,
                    'final_equity': equity
                }
        
        # Print results
        print("\nBacktest Results:")
        print("================")
        for symbol, stats in results.items():
            print(f"{symbol}:")
            print(f"  Trades: {stats['trades']}")
            print(f"  Win Rate: {stats['win_rate']:.2%}")
            print(f"  Profit Factor: {stats['profit_factor']:.2f}")
            print(f"  Final Equity: ${stats['final_equity']:.2f}")
            print("")


def main():
    """Main entry point for the signal engine."""
    parser = argparse.ArgumentParser(description='OpenMT4TradingBot Signal Engine')
    parser.add_argument('--mt4-path', type=str, help='Path to MT4 Files directory')
    parser.add_argument('--data-path', type=str, help='Path to data directory')
    parser.add_argument('--backtest', action='store_true', help='Run backtest')
    parser.add_argument('--update-cot', action='store_true', help='Update COT data and exit')
    parser.add_argument('--use-deepseek', action='store_true', help='Enable DeepSeek integration')
    
    args = parser.parse_args()
    
    # Create signal engine
    engine = SignalEngine(
        mt4_path=args.mt4_path,
        data_path=args.data_path,
        use_deepseek=args.use_deepseek
    )
    
    # Handle special modes
    if args.update_cot:
        engine.update_cot()
        return
        
    if args.backtest:
        engine.backtest()
        return
    
    # Main processing loop
    def run_process():
        try:
            engine.process_all_symbols()
            logger.info("Processing completed")
        except Exception as e:
            logger.error(f"Error in main process: {e}")
    
    # Initial run
    run_process()
    
    # Schedule regular updates
    schedule.every(UPDATE_INTERVAL_MINUTES).minutes.do(run_process)
    
    # Main loop
    logger.info(f"Signal engine running, checking every {UPDATE_INTERVAL_MINUTES} minutes")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Signal engine stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait a bit on error before retrying


if __name__ == "__main__":
    main()
