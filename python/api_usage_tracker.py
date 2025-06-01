#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API Usage Tracker per OpenMT4TradingBot.

Questo modulo fornisce funzionalità per monitorare l'utilizzo dell'API DeepSeek,
calcolare i costi associati e implementare strategie di throttling adattivo 
per mantenere i costi entro limiti predefiniti.

MIT License

Copyright (c) 2025 Immaginet Srl
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_usage_tracker")

# Constants
USAGE_DATA_DIR = Path("api_usage")
USAGE_DATA_FILE = USAGE_DATA_DIR / "usage_data.json"
MARKET_STATUS_FILE = USAGE_DATA_DIR / "market_status.json"

# Default settings
DEFAULT_DAILY_COST_LIMIT = 5.0  # $5 per day
DEFAULT_TOKEN_COST_PER_1K = 0.0002  # $0.0002 per 1K tokens
DEFAULT_THROTTLING_LEVELS = {
    "normal": 1.0,      # Nessuna restrizione (fattore 1.0)
    "light": 0.5,       # Riduzione al 50%
    "moderate": 0.3,    # Riduzione al 30%
    "heavy": 0.1,       # Riduzione al 10%
    "critical": 0.05    # Riduzione al 5%
}

# Configurazione per diversi tipi di analisi
ANALYSIS_CONFIG = {
    "news_bias": {
        "avg_tokens": 800,    # Token medi per richiesta
        "importance": 0.8,    # Importanza relativa (0-1)
        "interval_minutes": {
            "normal": 60,      # Ogni ora in condizioni normali
            "light": 120,      # Ogni 2 ore
            "moderate": 240,   # Ogni 4 ore
            "heavy": 480,      # Ogni 8 ore
            "critical": 720    # Ogni 12 ore
        }
    },
    "pattern_recognition": {
        "avg_tokens": 1200,
        "importance": 0.7,
        "interval_minutes": {
            "normal": 120,     # Ogni 2 ore
            "light": 240,      # Ogni 4 ore
            "moderate": 480,   # Ogni 8 ore
            "heavy": 720,      # Ogni 12 ore
            "critical": 1440   # Ogni 24 ore (1 giorno)
        }
    },
    "portfolio_optimization": {
        "avg_tokens": 2000,
        "importance": 0.6,
        "interval_minutes": {
            "normal": 240,     # Ogni 4 ore
            "light": 480,      # Ogni 8 ore
            "moderate": 720,   # Ogni 12 ore
            "heavy": 1440,     # Ogni 24 ore
            "critical": 2880   # Ogni 48 ore (2 giorni)
        }
    },
    "scenario_analysis": {
        "avg_tokens": 3000,
        "importance": 0.5,
        "interval_minutes": {
            "normal": 360,     # Ogni 6 ore
            "light": 720,      # Ogni 12 ore
            "moderate": 1440,  # Ogni 24 ore
            "heavy": 2880,     # Ogni 48 ore
            "critical": 4320   # Ogni 72 ore (3 giorni)
        }
    },
    "chat": {
        "avg_tokens": 1000,
        "importance": 0.9,     # Alta importanza (interazione diretta con l'utente)
        "interval_minutes": {
            "normal": 0,       # Nessun limite
            "light": 0,        # Nessun limite
            "moderate": 0,     # Nessun limite
            "heavy": 2,        # Almeno 2 minuti tra le richieste
            "critical": 5      # Almeno 5 minuti tra le richieste
        }
    }
}

class APIUsageTracker:
    """Classe per monitorare l'utilizzo dell'API e applicare throttling adattivo."""
    
    def __init__(self, daily_cost_limit: float = DEFAULT_DAILY_COST_LIMIT):
        """
        Inizializza il tracker di utilizzo API.
        
        Args:
            daily_cost_limit: Limite di costo giornaliero in dollari
        """
        self.daily_cost_limit = daily_cost_limit
        self.lock = threading.Lock()
        self.current_throttling_level = "normal"
        self.active_markets = set()
        self.last_requests = {}  # Timestamp delle ultime richieste per tipo
        
        # Assicurati che la directory esista
        USAGE_DATA_DIR.mkdir(exist_ok=True)
        
        # Carica i dati di utilizzo esistenti
        self._load_usage_data()
        self._load_market_status()
        
    def _load_usage_data(self):
        """Carica i dati di utilizzo dal file di storage."""
        try:
            if USAGE_DATA_FILE.exists():
                with open(USAGE_DATA_FILE, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = self._create_empty_usage_data()
                self._save_usage_data()
        except Exception as e:
            logger.error(f"Errore nel caricamento dei dati di utilizzo: {e}")
            self.usage_data = self._create_empty_usage_data()
    
    def _create_empty_usage_data(self):
        """Crea una struttura vuota per i dati di utilizzo."""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "days": {
                today: {
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "requests_count": 0,
                    "by_type": {}
                }
            },
            "current_month": {
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "requests_count": 0
            },
            "throttling": {
                "current_level": "normal",
                "last_updated": datetime.now().isoformat()
            },
            "last_request_time": datetime.now().isoformat()
        }
    
    def _save_usage_data(self):
        """Salva i dati di utilizzo nel file di storage."""
        try:
            with self.lock:
                with open(USAGE_DATA_FILE, 'w') as f:
                    json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Errore nel salvataggio dei dati di utilizzo: {e}")
    
    def _load_market_status(self):
        """Carica lo stato dei mercati dal file di storage."""
        try:
            if MARKET_STATUS_FILE.exists():
                with open(MARKET_STATUS_FILE, 'r') as f:
                    market_data = json.load(f)
                    self.active_markets = set(market_data.get("active_markets", []))
            else:
                self.active_markets = set()
                self._save_market_status()
        except Exception as e:
            logger.error(f"Errore nel caricamento dello stato dei mercati: {e}")
            self.active_markets = set()
    
    def _save_market_status(self):
        """Salva lo stato dei mercati nel file di storage."""
        try:
            with self.lock:
                market_data = {
                    "active_markets": list(self.active_markets),
                    "last_updated": datetime.now().isoformat()
                }
                with open(MARKET_STATUS_FILE, 'w') as f:
                    json.dump(market_data, f, indent=2)
        except Exception as e:
            logger.error(f"Errore nel salvataggio dello stato dei mercati: {e}")
    
    def update_active_markets(self, markets: List[str]):
        """
        Aggiorna l'elenco dei mercati attivi (con posizioni aperte o di interesse).
        
        Args:
            markets: Lista di simboli di mercato attivi
        """
        with self.lock:
            self.active_markets = set(markets)
            self._save_market_status()
    
    def is_market_active(self, market: str) -> bool:
        """
        Verifica se un mercato è considerato attivo.
        
        Args:
            market: Simbolo del mercato
        
        Returns:
            True se il mercato è attivo, False altrimenti
        """
        return market in self.active_markets
    
    def track_request(self, request_type: str, token_count: int, market: Optional[str] = None):
        """
        Registra una richiesta API completata.
        
        Args:
            request_type: Tipo di richiesta (es. "news_bias", "chat")
            token_count: Numero di token utilizzati
            market: Simbolo del mercato se applicabile
        """
        with self.lock:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Assicurati che la data odierna esista
            if today not in self.usage_data["days"]:
                self.usage_data["days"][today] = {
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "requests_count": 0,
                    "by_type": {}
                }
            
            # Aggiorna i dati del giorno
            self.usage_data["days"][today]["total_tokens"] += token_count
            cost = (token_count / 1000) * DEFAULT_TOKEN_COST_PER_1K
            self.usage_data["days"][today]["estimated_cost"] += cost
            self.usage_data["days"][today]["requests_count"] += 1
            
            # Aggiorna i dati per tipo
            if request_type not in self.usage_data["days"][today]["by_type"]:
                self.usage_data["days"][today]["by_type"][request_type] = {
                    "tokens": 0,
                    "count": 0,
                    "markets": {}
                }
            
            self.usage_data["days"][today]["by_type"][request_type]["tokens"] += token_count
            self.usage_data["days"][today]["by_type"][request_type]["count"] += 1
            
            # Aggiorna i dati per mercato se specificato
            if market:
                if market not in self.usage_data["days"][today]["by_type"][request_type]["markets"]:
                    self.usage_data["days"][today]["by_type"][request_type]["markets"][market] = {
                        "tokens": 0,
                        "count": 0
                    }
                
                self.usage_data["days"][today]["by_type"][request_type]["markets"][market]["tokens"] += token_count
                self.usage_data["days"][today]["by_type"][request_type]["markets"][market]["count"] += 1
            
            # Aggiorna i dati del mese
            self.usage_data["current_month"]["total_tokens"] += token_count
            self.usage_data["current_month"]["estimated_cost"] += cost
            self.usage_data["current_month"]["requests_count"] += 1
            
            # Aggiorna il timestamp dell'ultima richiesta
            self.usage_data["last_request_time"] = datetime.now().isoformat()
            self.last_requests[request_type] = time.time()
            
            # Ricalcola il livello di throttling in base all'utilizzo
            self._update_throttling_level()
            
            # Salva i dati aggiornati
            self._save_usage_data()
    
    def _update_throttling_level(self):
        """Aggiorna il livello di throttling in base all'utilizzo giornaliero."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cost = self.usage_data["days"].get(today, {}).get("estimated_cost", 0.0)
        
        # Determina il livello di throttling in base alla percentuale del limite giornaliero
        percent_of_limit = (daily_cost / self.daily_cost_limit) * 100
        
        if percent_of_limit < 50:
            new_level = "normal"
        elif percent_of_limit < 75:
            new_level = "light"
        elif percent_of_limit < 90:
            new_level = "moderate"
        elif percent_of_limit < 100:
            new_level = "heavy"
        else:
            new_level = "critical"
        
        if new_level != self.current_throttling_level:
            logger.info(f"Throttling level changed from {self.current_throttling_level} to {new_level} "
                       f"(Daily cost: ${daily_cost:.2f}, {percent_of_limit:.1f}% of limit)")
            self.current_throttling_level = new_level
            self.usage_data["throttling"]["current_level"] = new_level
            self.usage_data["throttling"]["last_updated"] = datetime.now().isoformat()
    
    def get_throttling_level(self) -> str:
        """
        Ottiene il livello di throttling corrente.
        
        Returns:
            Livello di throttling ("normal", "light", "moderate", "heavy", "critical")
        """
        return self.current_throttling_level
    
    def get_daily_usage(self) -> Dict:
        """
        Ottiene i dati di utilizzo del giorno corrente.
        
        Returns:
            Dizionario con i dati di utilizzo giornaliero
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return self.usage_data["days"].get(today, {
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "requests_count": 0,
            "by_type": {}
        })
    
    def should_execute_request(self, request_type: str, market: Optional[str] = None) -> bool:
        """
        Determina se una richiesta dovrebbe essere eseguita in base alle regole di throttling.
        
        Args:
            request_type: Tipo di richiesta (es. "news_bias", "chat")
            market: Simbolo del mercato se applicabile
        
        Returns:
            True se la richiesta dovrebbe procedere, False se dovrebbe essere saltata
        """
        # Chat è sempre permessa (alta priorità), ma con possibili limiti di frequenza
        if request_type == "chat":
            return self._check_request_interval(request_type)
        
        # Se il mercato è specificato e non è attivo, applica limitazioni più severe
        if market and not self.is_market_active(market):
            # Per mercati non attivi, esegui solo con una probabilità bassa basata sul livello di throttling
            throttle_factor = DEFAULT_THROTTLING_LEVELS.get(self.current_throttling_level, 1.0)
            # Riduce ulteriormente la probabilità per mercati non attivi
            market_factor = 0.2  # 20% della probabilità normale
            import random
            return random.random() < (throttle_factor * market_factor) and self._check_request_interval(request_type)
        
        # Per mercati attivi o richieste generiche, usa solo il controllo dell'intervallo
        return self._check_request_interval(request_type)
    
    def _check_request_interval(self, request_type: str) -> bool:
        """
        Verifica se è trascorso abbastanza tempo dall'ultima richiesta dello stesso tipo.
        
        Args:
            request_type: Tipo di richiesta
        
        Returns:
            True se l'intervallo minimo è rispettato, False altrimenti
        """
        if request_type not in ANALYSIS_CONFIG:
            return True  # Tipo di richiesta sconosciuto, permetti sempre
        
        # Ottieni l'intervallo minimo basato sul livello di throttling
        throttle_level = self.current_throttling_level
        min_interval_minutes = ANALYSIS_CONFIG[request_type]["interval_minutes"].get(throttle_level, 0)
        
        # Se l'intervallo è 0, non c'è limite di frequenza
        if min_interval_minutes == 0:
            return True
        
        # Controlla se è trascorso abbastanza tempo dall'ultima richiesta
        current_time = time.time()
        last_request_time = self.last_requests.get(request_type, 0)
        elapsed_minutes = (current_time - last_request_time) / 60
        
        return elapsed_minutes >= min_interval_minutes
    
    def get_usage_report(self) -> Dict:
        """
        Genera un report completo sull'utilizzo.
        
        Returns:
            Dizionario con il report di utilizzo
        """
        today = datetime.now().strftime("%Y-%m-%d")
        daily_data = self.usage_data["days"].get(today, {})
        
        return {
            "daily": {
                "total_tokens": daily_data.get("total_tokens", 0),
                "estimated_cost": daily_data.get("estimated_cost", 0.0),
                "requests_count": daily_data.get("requests_count", 0),
                "percent_of_limit": (daily_data.get("estimated_cost", 0.0) / self.daily_cost_limit) * 100
            },
            "monthly": {
                "total_tokens": self.usage_data["current_month"]["total_tokens"],
                "estimated_cost": self.usage_data["current_month"]["estimated_cost"],
                "requests_count": self.usage_data["current_month"]["requests_count"]
            },
            "throttling": {
                "current_level": self.current_throttling_level,
                "last_updated": self.usage_data["throttling"]["last_updated"]
            },
            "active_markets": list(self.active_markets)
        }
    
    def set_daily_cost_limit(self, limit: float):
        """
        Imposta un nuovo limite di costo giornaliero.
        
        Args:
            limit: Nuovo limite in dollari
        """
        with self.lock:
            self.daily_cost_limit = limit
            # Ricalcola il livello di throttling con il nuovo limite
            self._update_throttling_level()
            self._save_usage_data()
    
    def estimate_request_cost(self, request_type: str) -> Tuple[int, float]:
        """
        Stima il costo di una richiesta in base al tipo.
        
        Args:
            request_type: Tipo di richiesta
        
        Returns:
            Tupla (token_stimati, costo_stimato)
        """
        config = ANALYSIS_CONFIG.get(request_type, {"avg_tokens": 500})
        avg_tokens = config.get("avg_tokens", 500)
        cost = (avg_tokens / 1000) * DEFAULT_TOKEN_COST_PER_1K
        return avg_tokens, cost

# Istanza singleton per accesso globale
_instance = None

def get_instance() -> APIUsageTracker:
    """
    Ottiene l'istanza singleton di APIUsageTracker.
    
    Returns:
        Istanza di APIUsageTracker
    """
    global _instance
    if _instance is None:
        _instance = APIUsageTracker()
    return _instance

def track_api_call(request_type: str, token_count: int, market: Optional[str] = None):
    """
    Traccia una chiamata API completata.
    
    Args:
        request_type: Tipo di richiesta
        token_count: Numero di token utilizzati
        market: Simbolo del mercato se applicabile
    """
    tracker = get_instance()
    tracker.track_request(request_type, token_count, market)

def should_execute_api_call(request_type: str, market: Optional[str] = None) -> bool:
    """
    Determina se una chiamata API dovrebbe essere eseguita in base alle regole di throttling.
    
    Args:
        request_type: Tipo di richiesta
        market: Simbolo del mercato se applicabile
    
    Returns:
        True se la chiamata dovrebbe procedere, False altrimenti
    """
    tracker = get_instance()
    return tracker.should_execute_request(request_type, market)

def update_active_markets(markets: List[str]):
    """
    Aggiorna l'elenco dei mercati attivi.
    
    Args:
        markets: Lista di simboli di mercato attivi
    """
    tracker = get_instance()
    tracker.update_active_markets(markets)

def get_throttling_level() -> str:
    """
    Ottiene il livello di throttling corrente.
    
    Returns:
        Livello di throttling corrente
    """
    tracker = get_instance()
    return tracker.get_throttling_level()

def get_usage_report() -> Dict:
    """
    Ottiene un report completo sull'utilizzo.
    
    Returns:
        Dizionario con il report di utilizzo
    """
    tracker = get_instance()
    return tracker.get_usage_report()

def set_daily_cost_limit(limit: float):
    """
    Imposta un nuovo limite di costo giornaliero.
    
    Args:
        limit: Nuovo limite in dollari
    """
    tracker = get_instance()
    tracker.set_daily_cost_limit(limit)

if __name__ == "__main__":
    # Test code
    import argparse
    
    parser = argparse.ArgumentParser(description="API Usage Tracker per OpenMT4TradingBot")
    parser.add_argument("--report", action="store_true", help="Mostra il report di utilizzo")
    parser.add_argument("--set-limit", type=float, help="Imposta un nuovo limite di costo giornaliero")
    parser.add_argument("--add-markets", nargs="+", help="Aggiungi mercati attivi")
    parser.add_argument("--simulate", action="store_true", help="Simula una serie di chiamate API")
    
    args = parser.parse_args()
    
    if args.report:
        report = get_usage_report()
        print(json.dumps(report, indent=2))
    
    if args.set_limit:
        set_daily_cost_limit(args.set_limit)
        print(f"Limite di costo giornaliero impostato a ${args.set_limit:.2f}")
    
    if args.add_markets:
        update_active_markets(args.add_markets)
        print(f"Mercati attivi aggiornati: {args.add_markets}")
    
    if args.simulate:
        print("Simulazione di chiamate API...")
        
        # Simula una serie di chiamate API
        for i in range(10):
            request_type = "news_bias" if i % 3 == 0 else "chat" if i % 3 == 1 else "pattern_recognition"
            market = f"XAUUSD" if i % 2 == 0 else "WTICOUSD"
            
            should_execute = should_execute_api_call(request_type, market)
            print(f"Request {i+1}: {request_type} for {market} - Execute: {should_execute}")
            
            if should_execute:
                # Simula una chiamata API
                tokens = 500 if request_type == "chat" else 800 if request_type == "news_bias" else 1200
                track_api_call(request_type, tokens, market)
                
                # Mostra il livello di throttling
                print(f"  Throttling level: {get_throttling_level()}")
                
                # Pausa breve
                time.sleep(0.5)
        
        # Mostra il report finale
        report = get_usage_report()
        print("\nReport finale:")
        print(json.dumps(report, indent=2))
