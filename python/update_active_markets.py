#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script per aggiornare i mercati attivi nel sistema di throttling adattivo.

Questo script legge i dati di trading dal sistema MT4 e aggiorna l'elenco
dei mercati attivi nel tracker di utilizzo API, in modo che il sistema
di throttling possa dare priorità ai mercati con posizioni aperte o di
particolare interesse.

MIT License

Copyright (c) 2025 Immaginet Srl
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Set

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_active_markets")

# Importa il tracker di utilizzo API
import api_usage_tracker as usage_tracker

# Percorsi dei file di dati
SIGNAL_FILE = Path("data/signal.json")
POSITIONS_FILE = Path("data/positions.json")

def read_json_file(file_path: Path) -> Dict:
    """Legge un file JSON e restituisce il contenuto come dizionario."""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Errore nella lettura del file {file_path}: {e}")
        return {}

def get_active_markets() -> Set[str]:
    """
    Determina quali mercati sono attivi in base a:
    1. Posizioni attualmente aperte
    2. Mercati con segnali recenti
    3. Mercati di particolare interesse (configurabili)
    
    Returns:
        Set di simboli di mercato attivi
    """
    active_markets = set()
    
    # Controlla le posizioni aperte
    positions_data = read_json_file(POSITIONS_FILE)
    for position in positions_data.get("positions", []):
        symbol = position.get("symbol")
        if symbol:
            active_markets.add(symbol)
    
    # Controlla i segnali recenti
    signal_data = read_json_file(SIGNAL_FILE)
    for symbol, signal_info in signal_data.get("signals", {}).items():
        # Se il segnale è più recente di 3 giorni o è diverso da "neutral"
        signal_type = signal_info.get("signal", "neutral")
        if signal_type != "neutral":
            active_markets.add(symbol)
    
    # Aggiungi mercati di particolare interesse (predefiniti o configurati)
    # Qui potresti leggere da un file di configurazione o usare valori predefiniti
    default_markets_of_interest = ["XAUUSD", "XAGUSD"]  # Oro e Argento sempre monitorati
    active_markets.update(default_markets_of_interest)
    
    return active_markets

def update_tracker_with_active_markets():
    """Aggiorna il tracker di utilizzo API con l'elenco dei mercati attivi."""
    active_markets = get_active_markets()
    logger.info(f"Mercati attivi rilevati: {', '.join(active_markets)}")
    
    # Aggiorna il tracker
    usage_tracker.update_active_markets(list(active_markets))
    logger.info("Tracker di utilizzo API aggiornato con successo")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggiorna i mercati attivi nel tracker di utilizzo API")
    parser.add_argument("--force", action="store_true", help="Forza l'aggiornamento anche senza cambiamenti")
    args = parser.parse_args()
    
    update_tracker_with_active_markets()
