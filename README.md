# OpenMT4TradingBot

A hybrid MT4 + Python trading bot for commodities markets with DeepSeek AI integration. React Native Web Interface

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

#### Metodo automatico (consigliato)
1. Esegui lo script di installazione automatico:
   ```bash
   # Su Linux/macOS
   ./install_python.sh
   
   # Su Windows
   # Prima esegui: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install_python.sh
   ```

2. Lo script automaticamente:
   - Verifica che Python sia installato
   - Offre la possibilità di creare un ambiente virtuale
   - Installa tutte le dipendenze necessarie
   - Crea un file `.env` di esempio se non esiste

#### Metodo manuale
1. Crea un ambiente virtuale Python e attivalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   pip install fastapi uvicorn pydantic rich
   ```

3. Configura la chiave API DeepSeek:
   - Crea un file `.env` nella directory principale con la tua chiave API:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     DEEPSEEK_MODEL=deepseek-chat
     DEEPSEEK_API_BASE=https://api.deepseek.com/v1
     ```
   - Nota: Il file `.env` è incluso in `.gitignore` per evitare l'esposizione accidentale della chiave

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

### Avvio Semplificato (Raccomandato)

Utilizza lo script interattivo di controllo per avviare tutti i componenti Python con un'interfaccia user-friendly:

1. Avvia lo script di controllo:
   ```bash
   ./start_trading_bot.sh
   ```

2. Utilizza il menu interattivo per:
   - Avviare/arrestare tutti i servizi con un click
   - Avviare selettivamente il motore dei segnali, l'interfaccia chat o il server web
   - Generare grafici interattivi per le commodity
   - Controllare lo stato dei servizi
   - Visualizzare i log dei vari componenti

   ![Menu Interattivo](https://example.com/screenshots/menu.png)

3. Funzionalità principali:
   - **Avvio Automatizzato**: Gestisce l'ambiente virtuale e le dipendenze
   - **Monitoraggio Servizi**: Visualizza lo stato di tutti i componenti Python
   - **Generazione Grafici**: Interfaccia guidata per creare grafici interattivi
   - **Gestione Log**: Accesso facile ai log di tutti i componenti

### Avvio Manuale dei Componenti

1. Naviga alla directory principale del progetto:
   ```bash
   cd /path/to/OpenMT4TradingBot
   ```

2. Avvia il motore di segnali:
   ```bash
   python3 python/signal_engine.py
   ```

3. Opzioni disponibili:
   ```
   --mt4-path PATH     Percorso alla directory MT4 Files
   --data-path PATH    Percorso alla directory dei dati
   --backtest          Esegui backtest
   --update-cot        Aggiorna i dati COT ed esci
   --use-deepseek      Abilita l'integrazione con DeepSeek
   --compress=N        Imposta livello compressione cache (0-9, default: 6)
   --nocompress        Disabilita la compressione della cache
   ```

### Utilizzo dell'interfaccia chat

#### Server Web
1. Avvia il server web:
   ```bash
   python3 python/chat_interface.py --server --port 8000
   ```

2. Accedi all'API tramite browser:
   - Apri `http://localhost:8000` nel tuo browser

3. Oppure usa l'API REST:
   ```bash
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is the current bias on Gold?"}'
   ```

#### Interfaccia a Linea di Comando (CLI)
1. Fai una domanda direttamente:
   ```bash
   python3 python/chat_interface.py "Perché il bot ha chiuso la posizione long su WTI?"
   ```

2. Modalità interattiva:
   ```bash
   python3 python/chat_interface.py
   ```

3. Comandi speciali disponibili nell'interfaccia:
   - `/analyze [simbolo]` - Analizza i fattori di mercato
   - `/patterns [simbolo]` - Identifica pattern tecnici
   - `/news [simbolo]` - Mostra le ultime notizie
   - `/chart [simbolo] [periodo] [intervallo]` - Genera un grafico interattivo (es. `/chart XAUUSD 1y 1d`)
   - `/optimize` - Ottimizza il portafoglio
   - `/scenarios` - Analisi scenari di mercato

## File Structure

```
/OpenMT4TradingBot/              # Directory principale del progetto
  ├─ mql4/                     # Componenti MetaTrader 4
  │   └─ OpenMT4TradingBot.mq4 # Expert Advisor MT4 per l'esecuzione dei segnali di trading
  ├─ python/                   # Componenti Python del sistema
  │   ├─ signal_engine.py      # Motore principale per il calcolo dei segnali di trading
  │   ├─ deepseek_utils.py     # Utilities per l'integrazione con l'API DeepSeek
  │   ├─ chat_interface.py     # Interfaccia a riga di comando per comunicare con l'AI
  │   ├─ charting_utils.py     # Utilities per la generazione di grafici interattivi
  │   ├─ api_server.py         # Server API FastAPI per la comunicazione con la dashboard React
  │   ├─ requirements.txt      # Elenco delle dipendenze Python richieste
  │   └─ setup.py              # Script di configurazione per l'installazione
  ├─ web-dashboard/            # Interfaccia utente moderna basata su React
  │   ├─ package.json           # Configurazione del progetto React e dipendenze
  │   ├─ src/                   # Codice sorgente dell'applicazione React
  │   │   ├─ components/         # Componenti React modulari
  │   │   │   ├─ Dashboard.jsx     # Componente principale che organizza l'interfaccia
  │   │   │   ├─ TradingChart.jsx  # Grafico interattivo per visualizzare dati OHLC e segnali
  │   │   │   ├─ ApiUsageMonitor.jsx # Monitoraggio dell'utilizzo dell'API DeepSeek
  │   │   │   ├─ MarketOverview.jsx # Panoramica dei mercati con stato e filtri attivi
  │   │   │   ├─ SignalsTable.jsx   # Tabella dei segnali di trading con filtri
  │   │   │   └─ BotControls.jsx   # Controlli per avviare/fermare il bot e modificare le impostazioni
  │   │   ├─ pages/               # Pagine dell'applicazione React
  │   │   │   └─ index.jsx         # Pagina principale che carica il Dashboard
  │   │   ├─ styles/              # Fogli di stile CSS
  │   │   │   └─ styles.css        # Stile globale dell'applicazione
  │   │   ├─ api/                 # Funzioni per le chiamate API al backend
  │   │   ├─ hooks/               # Hook React personalizzati
  │   │   └─ utils/               # Funzioni di utilità condivise
  │   ├─ public/                # File statici pubblici (favicon, immagini, ecc.)
  │   └─ node_modules/          # Dipendenze JavaScript installate (generato automaticamente)
  ├─ data/                     # Dati utilizzati dal sistema
  │   ├─ cot.csv                # Dati COT (Commitment of Traders)
  │   ├─ season.json            # Configurazione della stagionalità per i vari mercati
  │   └─ signals.json           # File di output con i segnali di trading generati
  ├─ logs/                     # Directory per i file di log
  │   ├─ signal_engine.log      # Log del motore di segnali
  │   ├─ chat_interface.log     # Log dell'interfaccia chat
  │   ├─ api_server.log         # Log del server API
  │   └─ react_interface.log    # Log dell'interfaccia React
  ├─ install_python.sh         # Script per l'installazione dell'ambiente Python
  ├─ start_trading_bot.sh      # Script per avviare e gestire i componenti del trading bot
  ├─ start_dashboard.sh        # Script per avviare la dashboard React e il server API
  ├─ .env                      # File di configurazione per le variabili d'ambiente (API key)
  ├─ .gitignore                # Configurazione per escludere file dal controllo versione
  └─ README.md                # Documentazione del progetto
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
- Token usage is optimized with advanced caching system

### Ottimizzazioni Cache
- **Sistema di cache a due livelli**: Memoria (LRU) + Disco (JSON compresso)
- **Compressione GZIP**: Riduce spazio su disco fino al 70-80% per risposte API lunghe
- **Ottimizzazione delle chiavi di cache**:
  - Normalizzazione: elimina duplicati dovuti a case, spazi o caratteri speciali
  - Limitazione intelligente della lunghezza: tronca query lunghe mantenendo l'unicità
  - Organizzazione gerarchica: struttura ottimizzata in sottodirectory per tipo
  - Sharding dei file: distribuzione per evitare directory troppo popolate
- **TTL differenziati per tipo di dato**:
  - Chat responses: 10 minuti
  - Notizie: 1 ora
  - Analisi di mercato: 30 minuti
  - Riconoscimento pattern: 1 ora
  - Ottimizzazione portfolio: 20 minuti
  - Analisi di scenario: 30 minuti
- **Gestione automatica dello spazio**: Pulizia file scaduti e compressione adattiva quando lo spazio scarseggia

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

## Nuove Funzionalità

### Dashboard React Moderna

Abbiamo implementato una dashboard web moderna basata su React per monitorare e controllare il trading bot in tempo reale:

- **Interfaccia Responsive**: Design moderno che si adatta a dispositivi desktop e mobile
- **Grafici Interattivi**: Visualizzazione professionale di candlestick OHLC con indicatori Donchian
- **Monitoraggio API DeepSeek**: Visualizzazione in tempo reale dell'utilizzo e del throttling dell'API
- **Panoramica Mercati**: Stato attivo/inattivo di tutti i mercati supportati con filtri e segnali
- **Tabella Segnali**: Visualizzazione dettagliata dei segnali di trading con filtri e ordinamento
- **Controlli Bot**: Interfaccia per avviare/fermare il bot e configurare limiti di costo e soglie di throttling

Per avviare la dashboard, utilizzare il nuovo script `start_dashboard.sh`:

```bash
./start_dashboard.sh
```

### Grafici Interattivi per Commodity

Abbiamo integrato la visualizzazione di grafici interattivi per le commodity supportate:

- **Candlestick Charts**: Visualizzazione professionale dei dati OHLC
- **Indicatore di Volume**: Analisi del volume di trading integrata
- **Interattività**: Zoom, pan, e hover per analisi dettagliata
- **Timeframes Flessibili**: Da intraday a dati pluriennali
- **Accesso Multi-Piattaforma**:
  - Tramite interfaccia chat (`/chart XAUUSD 1y 1d`)
  - Attraverso il menu interattivo di `start_trading_bot.sh`
  - Direttamente tramite `charting_utils.py`
  - Nella nuova dashboard React (`start_dashboard.sh`)

### Interfaccia di Controllo Centralizzata

Il nuovo script `start_trading_bot.sh` fornisce un pannello di controllo unificato:

- **Menu Interattivo**: Semplice da usare anche per utenti non tecnici
- **Monitoraggio in Tempo Reale**: Visualizzazione dello stato di tutti i servizi
- **Gestione Log Centralizzata**: Accesso immediato ai log di tutti i componenti
- **Generazione Guidata dei Grafici**: Procedura guidata per generare grafici interattivi

## TODO and Future Improvements

- Add more sophisticated COT analysis
- Implement machine learning for adaptive parameters
- Add portfolio-level risk management
- Support for more trading instruments
- Add unit tests for all components
- Implement distributed cache for multi-instance deployments
- Add cache metrics dashboard for performance monitoring
- Enhance charting with technical indicators overlay
- Create a native desktop GUI using PyQt or similar
- Add WebSocket per aggiornamenti in tempo reale nella dashboard
- Aggiungere autenticazione e sicurezza per l'accesso alla dashboard

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