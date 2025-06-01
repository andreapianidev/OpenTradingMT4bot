# OpenMT4TradingBot

A hybrid MT4 + Python trading bot for commodities markets with DeepSeek AI integration.

## Overview

OpenMT4TradingBot is an open-source trading system that combines MetaTrader 4 (MT4) with Python to create a powerful commodities trading solution. The bot uses a Donchian breakout strategy with COT (Commitment of Traders) and seasonality filters to generate trading signals across multiple commodity markets.

The system is divided into two main components:
1. **MT4 Expert Advisor**: Handles trade execution, stop-loss/take-profit management, and data export
2. **Python Signal Engine**: Calculates trading signals, applies filters, and communicates with the EA via a file-based bridge

## Trading Strategy

OpenMT4TradingBot implements a sophisticated multi-factor trading approach designed specifically for commodities markets:

1. **Core Strategy - Donchian Breakout**: The system uses 40-bar Donchian channels on the D1 timeframe to identify significant price breakouts. This approach capitalizes on the tendency of commodities to experience sustained trends following range breakouts.

2. **Smart Filters**:
   - **COT Filter**: Analyzes CFTC's Commitment of Traders data to assess market positioning by different trader types (commercial hedgers, large speculators, small traders). This provides crucial insight into institutional sentiment and helps avoid trading against dominant market forces.
   - **Seasonality Filter**: Commodities often exhibit seasonal patterns due to production cycles, weather, and consumption patterns. The bot leverages historical seasonal tendencies to optimize entry timing and position sizing.

3. **Advanced Risk Management**:
   - **Adaptive Stop-Loss**: Uses Average True Range (ATR) to set stop-loss levels that adapt to current market volatility
   - **Intelligent Take-Profit**: Sets profit targets based on historical volatility and support/resistance levels
   - **Dynamic Trailing Stop**: Protects profits while allowing trends to develop fully
   - **Volatility-Based Position Sizing**: Adjusts position size based on ATR to maintain consistent risk across different commodities

4. **DeepSeek AI Enhancement**:
   - **Market Sentiment Analysis**: Evaluates news and market narratives to identify sentiment shifts
   - **Multi-Factor Market Analysis**: Combines technical, fundamental, and sentiment data
   - **Technical Pattern Recognition**: Identifies complex chart patterns that complement breakout signals
   - **Portfolio Optimization**: Suggests optimal allocation across multiple commodities
   - **Scenario Analysis**: Stress-tests strategies under different market conditions

## Why This Bot Is Valuable

- **Hybrid Architecture**: Combines MT4's reliable execution with Python's advanced analytics capabilities
- **Commodities Focus**: Specially designed for the unique characteristics of commodities markets
- **Multi-Factor Approach**: Integrates price action, market structure, sentiment, and seasonality
- **Intelligent Risk Management**: Adapts to changing market conditions with sophisticated risk controls
- **AI-Enhanced Decision Making**: Leverages DeepSeek AI for deeper market insights beyond traditional indicators
- **Conversation Interface**: Natural language interaction for traders to query the system about markets and strategy
- **Extensible Design**: Easy to customize and expand with additional strategies or commodities
- **Open Source**: Transparent implementation that can be audited and modified

## Features

- **Donchian Breakout Strategy**: Uses 40-bar Donchian channels on D1 timeframe
- **COT Filter**: Analyzes Commitment of Traders data for smart trade entries
- **Seasonal Filter**: Applies seasonality patterns to optimize position sizing
- **Risk Management**: ATR-based stop-loss, take-profit, and trailing stop
- **Volatility Parity**: Risk-adjusted position sizing based on ATR
- **DeepSeek AI Integration**: Sentiment analysis and natural language Q&A interface
- **File-Based Bridge**: Simple and reliable communication between MT4 and Python

## Supported Symbols

### Precious Metals
- Gold (XAUUSD)
- Silver (XAGUSD)
- Platinum (XPTUSD)
- Palladium (XPDUSD)

### Energy
- WTI Crude Oil (WTICOUSD)
- Brent Crude Oil (BCOUSD)
- Natural Gas (NATGASUSD)
- Heating Oil (HOIL)
- Gasoline RBOB (RBOB)

### Agricultural
- Corn (CORNUSD)
- Soybeans (SOYBNUSD)
- Wheat (WHEATUSD)
- Coffee (COFFEE)
- Cotton (COTTON)
- Sugar (SUGAR)
- Cocoa (COCOA)
- Orange Juice (OJ)

### Base Metals
- Copper (XCUUSD)
- Aluminum (XALUSD)
- Nickel (XNIUSD)
- Zinc (XZNUSD)
- Lead (XPBUSD)

## Requirements

### MetaTrader 4
- MT4 Platform (build 1320 or higher)
- MQL4 compiler

### Python
- Python 3.8 or higher
- Required packages:
  - pandas
  - numpy
  - requests
  - schedule
  - pyarrow
  - fastapi (optional, for web interface)
  - uvicorn (optional, for web interface)
  - rich (optional, for CLI interface)

## Installation

### MetaTrader 4 Setup
1. Copy `mql4/OpenMT4TradingBot.mq4` to your MT4 `MQL4/Experts` directory
2. Compile the EA in the MetaEditor
3. Create a directory `Files/OpenMT4TradingBot` in your MT4 data folder

### Python Setup
1. Install required packages:
   ```
   pip install pandas numpy requests schedule pyarrow
   ```

2. For optional DeepSeek integration:
   ```
   pip install fastapi uvicorn rich
   ```

3. Configure the DeepSeek API key:
   - Create a `.env` file in the project root with your API key:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     DEEPSEEK_MODEL=deepseek-chat
     DEEPSEEK_API_BASE=https://api.deepseek.com/v1
     ```
   - Note: The `.env` file is in `.gitignore` to prevent accidental key exposure

## Usage

### Starting the EA
1. Load the EA on a chart for one of the supported symbols
2. Configure the parameters:
   - BridgeMode: "FILE" (default file-based bridge)
   - RiskPercent: Risk percentage per trade (default 1%)
   - Lots: Fixed lot size (0 = auto calculation)
   - MagicNumber: Unique identifier for trades
   - UseTrailingStop: Enable/disable trailing stop
   - SignalCheckSeconds: Frequency of signal checks
   - ExportOHLC: Enable/disable OHLC data export
   - FilePath: Path for file operations

### Starting the Python Engine
1. Navigate to the python directory:
   ```
   cd python
   ```

2. Run the signal engine:
   ```
   python signal_engine.py
   ```

3. Optional flags:
   ```
   --mt4-path PATH     Path to MT4 Files directory
   --data-path PATH    Path to data directory
   --backtest          Run backtest
   --update-cot        Update COT data and exit
   --use-deepseek      Enable DeepSeek integration
   ```

### Using the Chat Interface

#### Web Server
1. Start the web server:
   ```
   python chat_interface.py --server --port 8000
   ```

2. Access the API:
   ```
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is the current bias on Gold?"}'
   ```

#### CLI Interface
1. Ask a question directly:
   ```
   python chat_interface.py "Why did the bot close the long position on WTI?"
   ```

2. Interactive mode:
   ```
   python chat_interface.py
   ```

## File Structure

```
/OpenMT4TradingBot/
  ├─ mql4/
  │   └─ OpenMT4TradingBot.mq4
  ├─ python/
  │   ├─ signal_engine.py
  │   ├─ deepseek_utils.py
  │   └─ chat_interface.py
  ├─ data/
  │   ├─ cot.csv
  │   └─ season.json
  ├─ .env
  ├─ .gitignore
  └─ README.md
```

## Strategy Details

### Entry Rules
- **Long Entry**: Close of yesterday equals highest high of last 40 bars
- **Short Entry**: Close of yesterday equals lowest low of last 40 bars

### Filters
- **COT Filter**:
  - Long only if Commercial net position ≤ -1σ below 3-year average
  - Short only if Commercial net position ≥ +1σ above 3-year average

- **Seasonal Filter**:
  - Normal position sizing if trade direction matches seasonal bias
  - Half position sizing if trade direction contradicts seasonal bias

### Exit Rules
- **Stop Loss**: 1.5 × ATR(20)
- **Take Profit**: 3.0 × ATR(20)
- **Trailing Stop**: Updates when price moves ≥ 1 ATR in favor

## DeepSeek AI Integration

The system includes AI-powered features through the DeepSeek API:

### News Sentiment Analysis
- Analyzes news headlines for trading bias
- Can adjust position sizing or skip trades based on sentiment
- Cached responses to minimize API usage

### Natural Language Q&A
- Query your trading system in plain language
- Example questions:
  - "Why did the bot enter a long position on gold?"
  - "What is the current COT data for silver?"
  - "How is my portfolio performing this month?"

### API Key Security
- Store your DeepSeek API key in the `.env` file
- This file is excluded from Git to prevent accidental exposure
- Token usage is optimized with caching (TTL: 300 seconds)

## Testing

### MT4 Strategy Tester
1. Open MT4 Strategy Tester
2. Select the EA
3. Configure settings:
   - Model: "Open prices only" or "Every tick"
   - Use date range covering multiple seasonal cycles
   - Visual mode for detailed analysis

### Python Backtest
Run the built-in backtest function:
```
python signal_engine.py --backtest
```

## TODO and Future Improvements

- Add more sophisticated COT analysis
- Implement machine learning for adaptive parameters
- Create a web dashboard for monitoring
- Add portfolio-level risk management
- Support for more trading instruments
- Add unit tests for all components

## License

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