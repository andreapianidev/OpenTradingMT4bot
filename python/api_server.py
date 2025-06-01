import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Aggiungi il percorso corrente al sys.path per importare i moduli locali
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa i moduli locali
from python import signal_engine
from python import api_usage_tracker
from python import deepseek_utils

# Configura il logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_server")

# Crea l'applicazione FastAPI
app = FastAPI(
    title="OpenMT4TradingBot API",
    description="API per il controllo e il monitoraggio di OpenMT4TradingBot",
    version="1.0.0"
)

# Abilita CORS per permettere richieste dall'interfaccia React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, limitare agli origine specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Istanza del motore dei segnali
signal_engine_instance = None
try:
    signal_engine_instance = signal_engine.SignalEngine()
    logger.info("SignalEngine inizializzato con successo")
except Exception as e:
    logger.error(f"Errore nell'inizializzazione di SignalEngine: {e}")

# Path per i file di dati
SIGNAL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "signal.json")

# Modelli di dati
class BotControlRequest(BaseModel):
    action: str  # 'start' o 'stop'

class ConfigUpdateRequest(BaseModel):
    daily_limit: Optional[float] = None
    deepseek_enabled: Optional[bool] = None

class ThrottlingConfigRequest(BaseModel):
    normal_threshold: Optional[float] = None
    light_threshold: Optional[float] = None
    moderate_threshold: Optional[float] = None
    heavy_threshold: Optional[float] = None
    inactive_market_multiplier: Optional[float] = None

# Stato del bot (in memoria)
bot_state = {
    "status": "stopped",
    "engine_status": "stopped",
    "chat_status": "stopped",
    "deepseek_enabled": True,
    "daily_limit": 5.0,
    "throttling_config": {
        "normal_threshold": 0.2,
        "light_threshold": 0.4,
        "moderate_threshold": 0.6,
        "heavy_threshold": 0.8,
        "inactive_market_multiplier": 2.0
    },
    "last_update": datetime.now().isoformat()
}

# Funzioni di utilità
def read_signal_file() -> Dict:
    """Legge il file dei segnali."""
    try:
        if os.path.exists(SIGNAL_FILE):
            with open(SIGNAL_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Errore nella lettura del file dei segnali: {e}")
        return {}

def get_ohlc_data(symbol: str, timeframe: str = "1d") -> Dict:
    """Ottiene i dati OHLC per un simbolo."""
    try:
        # Utilizzare yfinance per ottenere dati storici
        import yfinance as yf
        
        # Mapping dei timeframe
        tf_mapping = {
            "1h": "1h",
            "4h": "4h",
            "1d": "1d",
            "1w": "1wk"
        }
        
        # Converti il simbolo MT4 in un ticker Yahoo Finance
        yahoo_symbol = symbol
        if symbol == "XAUUSD":
            yahoo_symbol = "GC=F"  # Gold Futures
        elif symbol == "XAGUSD":
            yahoo_symbol = "SI=F"  # Silver Futures
        elif symbol == "WTICOUSD":
            yahoo_symbol = "CL=F"  # WTI Crude Oil
        elif symbol == "BCOUSD":
            yahoo_symbol = "BZ=F"  # Brent Crude Oil
        elif symbol == "NATGASUSD":
            yahoo_symbol = "NG=F"  # Natural Gas
        elif symbol == "CORNUSD":
            yahoo_symbol = "ZC=F"  # Corn Futures
        elif symbol == "SOYBNUSD":
            yahoo_symbol = "ZS=F"  # Soybean Futures
        elif symbol == "WHEATUSD":
            yahoo_symbol = "ZW=F"  # Wheat Futures
        
        # Scarica i dati
        data = yf.download(
            yahoo_symbol, 
            period="3mo", 
            interval=tf_mapping.get(timeframe, "1d"),
            progress=False
        )
        
        # Prepara i dati
        if data.empty:
            return {
                "dates": [],
                "ohlc": []
            }
            
        # Converti i dati in formato per il grafico
        dates = data.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
        ohlc = []
        
        for i in range(len(data)):
            ohlc.append({
                "open": data['Open'].iloc[i],
                "high": data['High'].iloc[i],
                "low": data['Low'].iloc[i],
                "close": data['Close'].iloc[i],
                "volume": data['Volume'].iloc[i] if 'Volume' in data.columns else 0
            })
        
        # Calcola l'indicatore Donchian
        if len(data) > 20:
            period = 20
            high_max = data['High'].rolling(window=period).max()
            low_min = data['Low'].rolling(window=period).min()
            
            donchian = {
                "upper": high_max.tolist(),
                "lower": low_min.tolist()
            }
        else:
            donchian = {
                "upper": [],
                "lower": []
            }
        
        # Leggi i segnali dal file
        signals_data = read_signal_file()
        signals = []
        
        if symbol in signals_data:
            signal_info = signals_data[symbol]
            if signal_info.get("signal") != "neutral":
                # Trova il prezzo più vicino nel set di dati
                signal_price = signal_info.get("entry", 0)
                signal_date = datetime.now().strftime('%Y-%m-%d')
                
                # Aggiungi il segnale
                signals.append({
                    "type": signal_info.get("signal", "neutral"),
                    "price": signal_price,
                    "date": signal_date
                })
        
        return {
            "dates": dates,
            "ohlc": ohlc,
            "donchian": donchian,
            "signals": signals
        }
    except Exception as e:
        logger.error(f"Errore nell'ottenimento dei dati OHLC per {symbol}: {e}")
        return {
            "dates": [],
            "ohlc": []
        }

def start_signal_engine(background_tasks: BackgroundTasks):
    """Avvia il motore dei segnali in background."""
    def run_signal_engine():
        global bot_state
        bot_state["engine_status"] = "running"
        
        try:
            if signal_engine_instance:
                # Esegui il calcolo dei segnali
                signal_engine_instance.process_all_symbols()
                logger.info("Calcolo dei segnali completato con successo")
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione del motore dei segnali: {e}")
        finally:
            bot_state["engine_status"] = "stopped"
    
    background_tasks.add_task(run_signal_engine)
    return {"status": "started"}

# Endpoint API
@app.get("/")
async def root():
    return {"message": "OpenMT4TradingBot API"}

@app.get("/api/active-markets")
async def get_active_markets():
    """Ottiene la lista dei mercati attivi."""
    try:
        active_markets = api_usage_tracker.get_active_markets()
        return {"markets": active_markets}
    except Exception as e:
        logger.error(f"Errore nell'ottenimento dei mercati attivi: {e}")
        return {"markets": []}

@app.get("/api/signals")
async def get_signals():
    """Ottiene i segnali di trading correnti."""
    return read_signal_file()

@app.get("/api/usage")
async def get_api_usage():
    """Ottiene le informazioni sull'utilizzo dell'API DeepSeek."""
    try:
        usage_report = api_usage_tracker.get_usage_report()
        throttling_level = api_usage_tracker.get_throttling_level()
        active_markets = api_usage_tracker.get_active_markets()
        
        return {
            "daily": usage_report.get("daily", {}),
            "monthly": usage_report.get("monthly", {}),
            "throttling": {
                "current_level": throttling_level
            },
            "active_markets": active_markets
        }
    except Exception as e:
        logger.error(f"Errore nell'ottenimento delle informazioni sull'utilizzo dell'API: {e}")
        return {
            "daily": {"total_tokens": 0, "estimated_cost": 0, "percent_of_limit": 0, "requests_count": 0},
            "monthly": {"total_tokens": 0, "estimated_cost": 0},
            "throttling": {"current_level": "normal"},
            "active_markets": []
        }

@app.get("/api/chart-data")
async def get_chart_data(symbol: str, timeframe: str = "1d"):
    """Ottiene i dati per il grafico di un simbolo."""
    return get_ohlc_data(symbol, timeframe)

@app.get("/api/bot-status")
async def get_bot_status():
    """Ottiene lo stato attuale del bot."""
    try:
        # Aggiorna lo stato del throttling
        throttling_level = api_usage_tracker.get_throttling_level()
        bot_state["throttling_config"]["current_level"] = throttling_level
        
        # Aggiorna il limite giornaliero
        import dotenv
        dotenv.load_dotenv()
        daily_limit = os.getenv("DEEPSEEK_DAILY_LIMIT", "5.0")
        bot_state["daily_limit"] = float(daily_limit)
        
        return bot_state
    except Exception as e:
        logger.error(f"Errore nell'ottenimento dello stato del bot: {e}")
        return bot_state

@app.post("/api/bot-control")
async def control_bot(request: BotControlRequest, background_tasks: BackgroundTasks):
    """Controlla l'avvio e l'arresto del bot."""
    global bot_state
    
    if request.action == "start":
        bot_state["status"] = "running"
        # Avvia il motore dei segnali
        start_signal_engine(background_tasks)
        return {"success": True, "message": "Bot avviato con successo"}
    elif request.action == "stop":
        bot_state["status"] = "stopped"
        return {"success": True, "message": "Bot arrestato con successo"}
    else:
        raise HTTPException(status_code=400, detail="Azione non valida")

@app.post("/api/update-config")
async def update_config(request: ConfigUpdateRequest):
    """Aggiorna la configurazione del bot."""
    global bot_state
    
    try:
        # Aggiorna il limite giornaliero
        if request.daily_limit is not None:
            bot_state["daily_limit"] = request.daily_limit
            # Aggiorna anche il file .env
            import dotenv
            dotenv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            dotenv.load_dotenv(dotenv_file)
            dotenv.set_key(dotenv_file, "DEEPSEEK_DAILY_LIMIT", str(request.daily_limit))
        
        # Aggiorna lo stato di DeepSeek
        if request.deepseek_enabled is not None:
            bot_state["deepseek_enabled"] = request.deepseek_enabled
            # Potrebbe essere necessario aggiornare un flag nel modulo deepseek_utils
        
        bot_state["last_update"] = datetime.now().isoformat()
        return {"success": True, "message": "Configurazione aggiornata con successo"}
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento della configurazione: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiornamento della configurazione: {str(e)}")

@app.post("/api/update-throttling")
async def update_throttling(request: ThrottlingConfigRequest):
    """Aggiorna la configurazione del throttling."""
    global bot_state
    
    try:
        # Aggiorna la configurazione del throttling
        if request.normal_threshold is not None:
            bot_state["throttling_config"]["normal_threshold"] = request.normal_threshold
            api_usage_tracker.set_threshold("normal", request.normal_threshold)
        
        if request.light_threshold is not None:
            bot_state["throttling_config"]["light_threshold"] = request.light_threshold
            api_usage_tracker.set_threshold("light", request.light_threshold)
        
        if request.moderate_threshold is not None:
            bot_state["throttling_config"]["moderate_threshold"] = request.moderate_threshold
            api_usage_tracker.set_threshold("moderate", request.moderate_threshold)
        
        if request.heavy_threshold is not None:
            bot_state["throttling_config"]["heavy_threshold"] = request.heavy_threshold
            api_usage_tracker.set_threshold("heavy", request.heavy_threshold)
        
        if request.inactive_market_multiplier is not None:
            bot_state["throttling_config"]["inactive_market_multiplier"] = request.inactive_market_multiplier
            api_usage_tracker.set_inactive_market_multiplier(request.inactive_market_multiplier)
        
        bot_state["last_update"] = datetime.now().isoformat()
        return {"success": True, "message": "Configurazione throttling aggiornata con successo"}
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento della configurazione throttling: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiornamento della configurazione throttling: {str(e)}")

# Monta i file statici della dashboard React
@app.on_event("startup")
async def startup_event():
    """Evento di avvio del server."""
    # Verifica la presenza della cartella della dashboard React
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web-dashboard/build")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        logger.info(f"Interfaccia React montata da {static_dir}")
    else:
        logger.warning(f"Directory dell'interfaccia React non trovata: {static_dir}")

# Avvio del server
if __name__ == "__main__":
    # Crea la directory dei log se non esiste
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
