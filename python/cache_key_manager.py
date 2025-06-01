#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache_key_manager.py - Gestione avanzata delle chiavi di cache per OpenMT4TradingBot

Questo modulo fornisce funzionalità specializzate per l'ottimizzazione delle chiavi di cache:
1. Normalizzazione delle chiavi per evitare duplicati (case-folding, rimozione spazi)
2. Limitazione della lunghezza per query molto lunghe
3. Organizzazione gerarchica in sottodirectory per tipo di dato
4. Generazione di hash deterministici per chiavi complesse

Copyright (c) 2025 Immaginet Srl
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta

# Configurazione logging
logger = logging.getLogger(__name__)

# Configurazione generale
MAX_KEY_LENGTH = 128  # Lunghezza massima per una chiave di cache
HASH_ALGORITHM = 'sha256'  # Algoritmo di hash per le chiavi
KEY_SEPARATOR = ':'  # Separatore utilizzato per comporre chiavi complesse

# Cartelle per tipi di cache
CACHE_TYPE_DIRS = {
    'default': 'general',
    'chat': 'conversations', 
    'news': 'news_data',
    'market_analysis': 'market_analytics',
    'pattern': 'technical_patterns',
    'portfolio': 'portfolio_data',
    'scenario': 'scenario_analysis',
    'seasonal': 'seasonal_patterns',
    'cot': 'cot_data',
    'backtest': 'backtest_results'
}

# Pattern regex per la pulizia delle chiavi
INVALID_CHARS_PATTERN = re.compile(r'[^\w\-\.]')
WHITESPACE_PATTERN = re.compile(r'\s+')
REPEAT_SEPARATORS = re.compile(r'_+')

class CacheKeyManager:
    """Gestore chiavi di cache con funzionalità avanzate di ottimizzazione."""
    
    def __init__(self, base_cache_dir: Path):
        """
        Inizializza il gestore chiavi di cache.
        
        Args:
            base_cache_dir: Directory base per la cache su disco
        """
        self.base_cache_dir = base_cache_dir
        self._init_cache_structure()
    
    def _init_cache_structure(self) -> None:
        """Inizializza la struttura di directory per i diversi tipi di cache."""
        for cache_type, dir_name in CACHE_TYPE_DIRS.items():
            cache_dir = self.base_cache_dir / dir_name
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Initialized cache directory for {cache_type}: {cache_dir}")
    
    def normalize_key(self, key: str) -> str:
        """
        Normalizza una chiave di cache per evitare duplicati.
        
        Args:
            key: Chiave originale da normalizzare
            
        Returns:
            Chiave normalizzata
        """
        # Conversione a lowercase e trim
        normalized = key.lower().strip()
        
        # Rimozione caratteri non validi
        normalized = INVALID_CHARS_PATTERN.sub('_', normalized)
        
        # Sostituzione whitespace con underscore singolo
        normalized = WHITESPACE_PATTERN.sub('_', normalized)
        
        # Rimozione underscore ripetuti
        normalized = REPEAT_SEPARATORS.sub('_', normalized)
        
        # Rimozione leading/trailing underscore
        normalized = normalized.strip('_')
        
        logger.debug(f"Normalized key from '{key}' to '{normalized}'")
        return normalized
    
    def truncate_key(self, key: str, max_length: int = MAX_KEY_LENGTH) -> str:
        """
        Tronca una chiave mantenendo significatività.
        
        Per chiavi lunghe, viene generato un hash della parte in eccesso
        e concatenato alla parte iniziale per mantenere leggibilità.
        
        Args:
            key: Chiave da troncare
            max_length: Lunghezza massima
            
        Returns:
            Chiave troncata con hash
        """
        if len(key) <= max_length:
            return key
            
        # Per chiavi troppo lunghe, prendiamo l'inizio e un hash della parte rimanente
        # Questo mantiene leggibilità ma garantisce unicità
        prefix_length = max_length // 2
        remaining = key[prefix_length:]
        
        # Genera hash della parte rimanente
        hash_obj = hashlib.new(HASH_ALGORITHM)
        hash_obj.update(remaining.encode('utf-8'))
        hash_digest = hash_obj.hexdigest()[:max_length - prefix_length - 1]
        
        truncated = f"{key[:prefix_length]}_{hash_digest}"
        logger.debug(f"Truncated key from {len(key)} chars to {len(truncated)}")
        
        return truncated
    
    def get_cache_path(self, key: str, cache_type: str = "default") -> Path:
        """
        Ottieni il percorso file per una chiave di cache.
        
        Args:
            key: Chiave di cache originale
            cache_type: Tipo di cache (influenza sottodirectory)
            
        Returns:
            Path al file di cache
        """
        # Normalizza e tronca la chiave
        normalized = self.normalize_key(key)
        truncated = self.truncate_key(normalized)
        
        # Determina sottodirectory appropriata
        subdir_name = CACHE_TYPE_DIRS.get(cache_type, CACHE_TYPE_DIRS['default'])
        cache_subdir = self.base_cache_dir / subdir_name
        
        # Ulteriore organizzazione in sottocartelle basata su prefisso per evitare
        # troppe cartelle nello stesso livello (sharding)
        prefix = truncated[:2] if len(truncated) >= 2 else 'aa'
        sharded_dir = cache_subdir / prefix
        sharded_dir.mkdir(exist_ok=True)
        
        # Genera il percorso completo
        return sharded_dir / f"{truncated}.cache.gz"
    
    def compose_key(self, *parts, prefix: str = None) -> str:
        """
        Compone una chiave multi-parte per query complesse.
        
        Args:
            *parts: Parti della chiave
            prefix: Prefisso opzionale
            
        Returns:
            Chiave composta
        """
        # Filtra parti vuote
        key_parts = [str(part) for part in parts if part]
        
        # Aggiungi prefisso se specificato
        if prefix:
            key_parts.insert(0, prefix)
            
        # Unisci le parti
        key = KEY_SEPARATOR.join(key_parts)
        
        return key
    
    def create_query_key(self, query: str, model: str = None, params: Dict = None) -> str:
        """
        Crea una chiave ottimizzata per query AI/DeepSeek.
        
        Args:
            query: Testo query principale
            model: Modello AI usato
            params: Parametri aggiuntivi che influenzano la risposta
            
        Returns:
            Chiave ottimizzata per la query
        """
        # Estrai parametri chiave che influenzano la risposta
        key_params = []
        
        if params:
            # Solo alcuni parametri influenzano veramente la risposta e dovrebbero
            # essere inclusi nella chiave di cache
            important_params = ['temperature', 'top_p', 'max_tokens']
            for param in important_params:
                if param in params:
                    key_params.append(f"{param}={params[param]}")
        
        # Componi la chiave
        model_part = model if model else "default_model"
        params_part = "_".join(key_params) if key_params else ""
        
        # Normalizza e tronca la query (spesso molto lunga)
        query_normalized = self.normalize_key(query)
        query_truncated = self.truncate_key(query_normalized, MAX_KEY_LENGTH // 2)
        
        return self.compose_key(model_part, params_part, query_truncated)
    
    def get_metadata_path(self, cache_path: Path) -> Path:
        """
        Ottieni il percorso per i metadati associati a una cache.
        
        Args:
            cache_path: Percorso al file di cache
            
        Returns:
            Percorso al file di metadati
        """
        return cache_path.with_suffix('.meta.json')
    
    def generate_key_stats(self) -> Dict:
        """
        Genera statistiche sulle chiavi di cache attuali.
        
        Returns:
            Dizionario con statistiche per tipo di cache
        """
        stats = {}
        
        for cache_type, dir_name in CACHE_TYPE_DIRS.items():
            cache_dir = self.base_cache_dir / dir_name
            if not cache_dir.exists():
                continue
                
            # Conta i file per questo tipo
            count = sum(1 for _ in cache_dir.glob('**/*.cache.gz'))
            
            # Calcola dimensione totale
            size = sum(f.stat().st_size for f in cache_dir.glob('**/*.cache.gz') if f.is_file())
            
            stats[cache_type] = {
                'count': count,
                'size_kb': size / 1024,
                'avg_size_kb': (size / count) / 1024 if count > 0 else 0
            }
            
        return stats


def get_query_hash(query: str) -> str:
    """
    Genera un hash deterministico per una query.
    Utile per chiavi di identificazione univoche.
    
    Args:
        query: Query di cui generare l'hash
        
    Returns:
        Hash della query in formato esadecimale
    """
    hash_obj = hashlib.new(HASH_ALGORITHM)
    hash_obj.update(query.encode('utf-8'))
    return hash_obj.hexdigest()


def sanitize_filename(name: str) -> str:
    """
    Sanitizza una stringa per uso come nome file sicuro.
    
    Args:
        name: Nome originale
        
    Returns:
        Nome sanitizzato
    """
    # Rimuovi caratteri non sicuri per filesystem
    s = re.sub(r'[^\w\-\.]', '_', name)
    # Limita lunghezza
    return s[:255]  # Massima lunghezza su molti filesystem


if __name__ == "__main__":
    # Test del modulo
    import argparse
    
    # Configurazione logging per test
    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(description="Test del gestore chiavi di cache")
    parser.add_argument("--test", action="store_true", help="Esegui test")
    parser.add_argument("--cache-dir", type=str, default="./cache", help="Directory cache")
    args = parser.parse_args()
    
    if args.test:
        # Inizializza gestore
        key_manager = CacheKeyManager(Path(args.cache_dir))
        
        # Test chiavi
        test_keys = [
            "Una query normale",
            "QUERY CON MAIUSCOLE e spazi   multipli",
            "Query-con!caratteri@speciali#non$validi",
            "Query molto lunga " + "blah " * 100,
            "Query * with / invalid \\ chars & for % filename"
        ]
        
        for key in test_keys:
            normalized = key_manager.normalize_key(key)
            truncated = key_manager.truncate_key(normalized)
            cache_path = key_manager.get_cache_path(key, "chat")
            
            print(f"\nKey: {key}")
            print(f"Normalized: {normalized}")
            print(f"Truncated: {truncated}")
            print(f"Cache path: {cache_path}")
            
        # Test chiave query complessa
        complex_query = "Qual è l'impatto dei dati COT sul prezzo dell'oro?"
        query_key = key_manager.create_query_key(
            complex_query, 
            "deepseek-chat", 
            {"temperature": 0.7, "max_tokens": 1000}
        )
        cache_path = key_manager.get_cache_path(query_key, "market_analysis")
        
        print(f"\nComplex query: {complex_query}")
        print(f"Query key: {query_key}")
        print(f"Cache path: {cache_path}")
        
        # Statistiche chiavi
        print("\nGenerating structure...")
        for cache_type in CACHE_TYPE_DIRS:
            # Crea alcuni file di test
            for i in range(3):
                test_path = key_manager.get_cache_path(f"test_{i}", cache_type)
                test_path.parent.mkdir(parents=True, exist_ok=True)
                with open(test_path, "w") as f:
                    f.write(f"Test content for {cache_type}")
        
        # Mostra statistiche
        print("\nCache key statistics:")
        stats = key_manager.generate_key_stats()
        for cache_type, type_stats in stats.items():
            print(f"  {cache_type}: {type_stats['count']} files, "
                  f"{type_stats['size_kb']:.2f} KB total, "
                  f"{type_stats['avg_size_kb']:.2f} KB avg")
