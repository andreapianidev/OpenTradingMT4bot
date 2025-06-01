#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DeepSeek integration utilities for OpenMT4TradingBot.

This module provides functions to interact with the DeepSeek AI API
for sentiment analysis and natural language Q&A about trading data.

MIT License

Copyright (c) 2025 Immaginet Srl
"""

import os
import time
import json
import gzip
import random
import logging
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# Importa il tracker di utilizzo API
import api_usage_tracker as usage_tracker

# Importa il gestore delle chiavi di cache
from cache_key_manager import CacheKeyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deepseek_utils")

# Constants
CACHE_DIR = Path("cache")
DEFAULT_MODEL = "deepseek-chat"  # or "deepseek-reasoner"

# Cache settings (in seconds)
CACHE_TTL = {
    "default": 300,            # 5 minutes for general queries
    "chat": 600,               # 10 minutes for chat responses
    "news": 3600,              # 1 hour for news data
    "market_analysis": 1800,   # 30 minutes for market analysis
    "pattern": 3600,           # 1 hour for pattern recognition
    "portfolio": 1200,         # 20 minutes for portfolio optimization
    "scenario": 1800,          # 30 minutes for scenario analysis
}

# Cache size limits
MAX_MEMORY_CACHE_ITEMS = 100
MAX_DISK_CACHE_SIZE_MB = 100

# Compression settings
COMPRESSION_ENABLED = True
COMPRESSION_LEVEL = 6  # 0-9, where 9 is max compression (but slower)
COMPRESSION_THRESHOLD = 1024  # Only compress items larger than this many bytes

# Inizializza il gestore delle chiavi di cache
cache_key_manager = CacheKeyManager(CACHE_DIR)

# News API settings
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_BASE = "https://newsapi.org/v2/everything"

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)

# In-memory LRU cache
MEMORY_CACHE = {}

# Load API key and base URL from environment variables
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MODEL = os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)

# Configura il logger anche per il cache key manager
logging.getLogger('cache_key_manager').setLevel(logging.INFO)

# Imposta il limite di costo giornaliero (configurable tramite .env)
DAILY_COST_LIMIT = float(os.environ.get("DEEPSEEK_DAILY_LIMIT", "5.0"))  # Default $5/giorno
usage_tracker.set_daily_cost_limit(DAILY_COST_LIMIT)

def _get_cache_path(cache_key: str, cache_type: str = "default") -> Path:
    """Get cache file path for a given key and type.
    
    Args:
        cache_key: The unique key for the cached data
        cache_type: Type of cached data (affects subdirectory and TTL)
        
    Returns:
        Path object for the cache file
    """
    # Usa il gestore delle chiavi di cache per ottenere un percorso ottimizzato
    return cache_key_manager.get_cache_path(cache_key, cache_type)


def _clean_cache():
    """Clean up old cache files and enforce size limits."""
    # Check if we need to clean up (do this occasionally, not on every access)
    if random.random() < 0.05:  # 5% chance to trigger cleanup
        try:
            # Delete expired files
            current_time = time.time()
            
            # Check and enforce total cache size
            total_size = 0
            file_info = []
            
            # Gather info about all cache files
            for cache_type_dir in CACHE_DIR.iterdir():
                if not cache_type_dir.is_dir():
                    continue
                    
                for cache_file in cache_type_dir.iterdir():
                    if not cache_file.is_file():
                        continue
                        
                    file_stat = cache_file.stat()
                    file_age = current_time - file_stat.st_mtime
                    file_size = file_stat.st_size
                    total_size += file_size
                    
                    # Get the cache type from directory name
                    cache_type = cache_type_dir.name
                    ttl = CACHE_TTL.get(cache_type, CACHE_TTL["default"])
                    
                    # Delete expired files immediately
                    if file_age > ttl:
                        cache_file.unlink(missing_ok=True)
                    else:
                        file_info.append((cache_file, file_age, file_size))
            
            # Check if we're over the size limit (convert MB to bytes)
            max_size_bytes = MAX_DISK_CACHE_SIZE_MB * 1024 * 1024
            if total_size > max_size_bytes:
                # Sort by age (oldest first)
                file_info.sort(key=lambda x: x[1], reverse=True)
                
                # Delete oldest files until we're under the limit
                deleted_count = 0
                freed_space = 0
                for file_path, _, file_size in file_info:
                    if total_size <= max_size_bytes:
                        break
                    file_path.unlink(missing_ok=True)
                    total_size -= file_size
                    deleted_count += 1
                    freed_space += file_size
                    
                logger.info(f"Cache cleanup completed. Deleted {deleted_count} files, freed {freed_space/1024:.1f} KB. New size: {total_size/(1024*1024):.2f} MB")
                
                # Re-compress large files if we're still over the limit
                if total_size > max_size_bytes * 0.9 and COMPRESSION_ENABLED:
                    # Get uncompressed files or files compressed at lower levels
                    for cache_type_dir in CACHE_DIR.iterdir():
                        if not cache_type_dir.is_dir():
                            continue
                            
                        for cache_file in cache_type_dir.iterdir():
                            if not cache_file.is_file() or not cache_file.name.endswith('.cache.gz'):
                                continue
                                
                            # Try to recompress with higher compression level
                            try:
                                # Read the current compressed data
                                with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                                    data = json.load(f)
                                    
                                # Recompress with maximum compression level
                                with gzip.open(cache_file, 'wt', encoding='utf-8', compresslevel=9) as f:
                                    f.write(json.dumps(data))
                                    
                                logger.debug(f"Recompressed {cache_file} with max compression")
                            except Exception as e:
                                logger.warning(f"Failed to recompress {cache_file}: {e}")
                    
                    # Calculate new size
                    new_total_size = sum(f.stat().st_size for f in Path(CACHE_DIR).glob('**/*') if f.is_file())
                    logger.info(f"After recompression: {new_total_size/(1024*1024):.2f} MB")
                
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")

def _get_from_cache(cache_key: str, cache_type: str = "default", extended_ttl: bool = False) -> Optional[Any]:
    """Retrieve data from cache if it exists and is not expired.
    
    Args:
        cache_key: The unique key for the cached data
        cache_type: Type of cached data (affects TTL)
        extended_ttl: If True, accept cache entries with longer TTL for throttling scenarios
        
    Returns:
        The cached data if found and valid, None otherwise
    """
    # Normalizza la chiave per consistenza
    normalized_key = cache_key_manager.normalize_key(cache_key)
    
    # First check in-memory cache (fastest)
    memory_key = f"{cache_type}:{normalized_key}"
    if memory_key in MEMORY_CACHE:
        cache_entry = MEMORY_CACHE[memory_key]
        # Check if in-memory cache has expired
        ttl = CACHE_TTL.get(cache_type, CACHE_TTL["default"])
        # Use extended TTL if requested (for throttling)
        if extended_ttl:
            ttl *= 2  # Double the TTL for throttling
            
        if time.time() - cache_entry['timestamp'] <= ttl:
            logger.debug(f"Memory cache hit for {cache_type}:{normalized_key}")
            return cache_entry['data']
        else:
            # Remove expired entry
            del MEMORY_CACHE[memory_key]
            logger.debug(f"Memory cache expired for {cache_type}:{normalized_key}")
    
    # Check disk cache
    cache_path = _get_cache_path(cache_key, cache_type)
    
    if not cache_path.exists():
        return None
    
    # Check TTL based on cache type
    if not _is_cache_valid(cache_path, cache_type, extended_ttl):
        logger.debug(f"Disk cache expired for {cache_type}:{cache_key}")
        return None
    
    try:
        # Read compressed data and decompress
        with gzip.open(cache_path, 'rt', encoding='utf-8') as f:
            cached_data = json.load(f)
            
            return None
        
        # Update memory cache
        MEMORY_CACHE[memory_key] = {
            'timestamp': cached_data['timestamp'],
            'data': cached_data['data']
        }
        
        # Manage memory cache size
        if len(MEMORY_CACHE) > MAX_MEMORY_CACHE_ITEMS:
            # Remove oldest item (simplistic approach)
            oldest_key = min(MEMORY_CACHE.keys(), key=lambda k: MEMORY_CACHE[k]['timestamp'])
            del MEMORY_CACHE[oldest_key]
            
        return cached_data['data']
    except Exception as e:
        logger.warning(f"Failed to read from cache: {e}")
        return None


def _is_cache_valid(cache_path: Path, cache_type: str, extended_ttl: bool = False) -> bool:
    """Check if a cache file is valid based on its age and type.
    
    Args:
        cache_path: Path to the cache file
        cache_type: Type of cache (affects TTL)
        extended_ttl: If True, use a longer TTL for throttling scenarios
        
    Returns:
        True if the cache is valid, False otherwise
    """
    # Get the cache TTL based on type
    ttl = CACHE_TTL.get(cache_type, CACHE_TTL["default"])
    
    # Use an extended TTL for throttling scenarios if requested
    if extended_ttl:
        ttl *= 2  # Double the TTL for throttling
    
    # Check the cache file's age
    file_age = time.time() - cache_path.stat().st_mtime
    
    return file_age <= ttl

def _save_to_cache(cache_key: str, data: Any, cache_type: str = "default") -> bool:
    """Save data to cache with current timestamp.
    
    Args:
        cache_key: The unique key for the cached data
        data: The data to cache
        cache_type: Type of cached data (affects storage location)
        
    Returns:
        True if successfully cached, False otherwise
    """
    # Occasionally clean the cache
    _clean_cache()
    
    # Skip caching if data is None
    if data is None:
        return False
    
    # Normalizza la chiave per consistenza
    normalized_key = cache_key_manager.normalize_key(cache_key)
    
    # Update memory cache
    memory_key = f"{cache_type}:{normalized_key}"
    timestamp = time.time()
    MEMORY_CACHE[memory_key] = {
        'timestamp': timestamp,
        'data': data
    }
    
    # Manage memory cache size
    if len(MEMORY_CACHE) > MAX_MEMORY_CACHE_ITEMS:
        # Remove oldest item
        oldest_key = min(MEMORY_CACHE.keys(), key=lambda k: MEMORY_CACHE[k]['timestamp'])
        del MEMORY_CACHE[oldest_key]
    
    # Update disk cache
    cache_path = _get_cache_path(cache_key, cache_type)
    
    try:
        # Prepare the data to be cached
        cache_data = {
            'timestamp': timestamp,
            'data': data
        }
        
        # Convert to JSON string first to determine size
        json_data = json.dumps(cache_data)
        data_size = len(json_data.encode('utf-8'))
        
        # Use compression for data over the threshold size
        if COMPRESSION_ENABLED and data_size > COMPRESSION_THRESHOLD:
            with gzip.open(cache_path, 'wt', encoding='utf-8', compresslevel=COMPRESSION_LEVEL) as f:
                # We don't need indentation with compression to save space
                f.write(json_data)
                logger.debug(f"Compressed cache ({data_size} bytes) for {cache_type}:{normalized_key}")
        else:
            # For small data, we can use pretty printing for better readability if needed manually
            with gzip.open(cache_path, 'wt', encoding='utf-8', compresslevel=COMPRESSION_LEVEL) as f:
                json.dump(cache_data, f, indent=2)
                
        return True
    except Exception as e:
        logger.warning(f"Failed to write to cache: {e}")
        return False


def deepseek_chat(messages: List[Dict], model: str = None, temperature: float = 0.7, 
                 max_tokens: int = 1000, offline: bool = False, cache_type: str = "chat",
                 market: Optional[str] = None) -> str:
    """
    Send a chat request to the DeepSeek API with adaptive throttling.
    
    Args:
        messages: List of message dictionaries in OpenAI format
                 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        model: Model name to use
        temperature: Temperature parameter for generation
        max_tokens: Maximum tokens to generate
        offline: If True, return a fallback response without making an API call
        cache_type: Type of cache to use (affects TTL)
        market: Symbol of the market this request is related to, if applicable
        
    Returns:
        str: Response from the DeepSeek API
    """
    request_type = cache_type  # Usiamo il tipo di cache come tipo di richiesta
    
    if offline:
        return "DeepSeek API is in offline mode. This is a fallback response."
        
    if not API_KEY:
        return "DeepSeek API key not configured. Set the DEEPSEEK_API_KEY environment variable."
    
    # Normalize model name
    if not model:
        model = MODEL if MODEL else DEFAULT_MODEL
    
    # Create cache key from the request parameters
    # Only include first 100 chars of each message to avoid excessively long keys
    sanitized_messages = []
    for msg in messages:
        sanitized_msg = {k: v[:100] + '...' if isinstance(v, str) and len(v) > 100 else v 
                        for k, v in msg.items()}
        sanitized_messages.append(sanitized_msg)
    
    cache_key = str(hash(str(sanitized_messages) + str(model) + str(temperature) + str(max_tokens)))
    
    # Check cache first
    cached_response = _get_from_cache(cache_key, cache_type)
    if cached_response:
        logger.info(f"Using cached DeepSeek response for {cache_type}")
        return cached_response
    
    # Verifica se la richiesta dovrebbe essere eseguita in base alle regole di throttling
    if not usage_tracker.should_execute_api_call(request_type, market):
        logger.warning(f"Throttling: Skipping API call for {request_type}" + 
                      (f" on {market}" if market else ""))
        
        # Se è una richiesta di tipo 'chat', genera una risposta personalizzata
        if cache_type == "chat":
            throttling_level = usage_tracker.get_throttling_level()
            usage_report = usage_tracker.get_usage_report()
            daily_cost = usage_report["daily"]["estimated_cost"]
            percent = usage_report["daily"]["percent_of_limit"]
            
            return (f"I'm currently operating in '{throttling_level}' throttling mode to control API costs. "
                   f"Daily usage is ${daily_cost:.2f} ({percent:.1f}% of limit). "
                   f"For non-critical queries, please try again later.")
        
        # Per altri tipi di richiesta, usa semplicemente una cache più lunga se possibile
        # o ritorna una risposta neutra appropriata per il tipo
        extended_cached_response = _get_from_cache(cache_key, cache_type, extended_ttl=True)
        if extended_cached_response:
            logger.info(f"Throttling: Using extended cache for {cache_type}")
            return extended_cached_response
            
        if cache_type == "news_bias":
            return ("neutral", 0.5)  # Valore neutro per news_bias
        
        return "API request throttled to control costs. Using fallback response."
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model or MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
            return f"Sorry, unavailable. API error: {response.status_code}"
            
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Stima il conteggio token in ingresso e uscita
        # Metodo semplice: circa 4 caratteri per token
        input_token_estimate = sum(len(str(msg.get("content", ""))) // 4 for msg in messages)
        output_token_estimate = len(content) // 4
        total_tokens = input_token_estimate + output_token_estimate
        
        # Traccia l'utilizzo dell'API
        usage_tracker.track_api_call(request_type, total_tokens, market)
        
        # Cache the successful response
        _save_to_cache(cache_key, content)
        
        return content
        
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {e}")
        return "Sorry, unavailable. An error occurred while connecting to the API."


def news_bias(symbol: str, headlines: List[str], offline: bool = False) -> Tuple[str, float]:
    """
    Analyze news headlines for trading bias on a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'XAUUSD')
        headlines: List of recent news headlines
        offline: If True, return a fallback response without making an API call
        
    Returns:
        Tuple of (bias, confidence) where:
            bias is one of: 'bullish', 'bearish', 'neutral'
            confidence is a float from 0.0 to 1.0
    """
    if not headlines:
        return ("neutral", 0.0)
        
    if offline:
        # Return random bias and confidence for testing
        import random
        biases = ["bullish", "bearish", "neutral"]
        return (random.choice(biases), random.random())
    
    # Crea una chiave più efficiente basata su symbol e headlines
    headlines_str = ",".join(headlines)
    headlines_hash = cache_key_manager.get_query_hash(headlines_str)[:16]
    cache_key = cache_key_manager.compose_key("news_bias", symbol, headlines_hash)
    
    # Try to get from cache
    cached_result = _get_from_cache(cache_key, "news")
    if cached_result is not None:
        logger.info(f"Using cached news bias analysis for {symbol}")
        return cached_result
    
    # Verifica se la richiesta dovrebbe essere eseguita in base alle regole di throttling
    if not usage_tracker.should_execute_api_call("news_bias", symbol):
        logger.warning(f"Throttling: Skipping news_bias API call for {symbol}")
        
        # Prova ad utilizzare una cache estesa
        extended_cached_result = _get_from_cache(cache_key, "news", extended_ttl=True)
        if extended_cached_result is not None:
            logger.info(f"Throttling: Using extended cache for news_bias on {symbol}")
            return extended_cached_result
        
        # Se non c'è una cache estesa, restituisci un valore neutro
        logger.info(f"Throttling: Using neutral fallback for news_bias on {symbol}")
        return ("neutral", 0.5)  # Valore neutro con confidenza media
    
    try:
        prompt = f"""
        Analyze these recent news headlines about {symbol} and determine if the overall sentiment is bullish, bearish, or neutral.
        Return your analysis as a JSON object with 'bias' (one of: 'bullish', 'bearish', 'neutral') and 'confidence' (0.0 to 1.0).
        
        Headlines:
        {headlines}
        
        Only respond with the JSON object, no other text:
        """
        
        messages = [
            {"role": "system", "content": "You are a financial news analyst specializing in commodity markets."},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_chat(messages, temperature=0.1, market=symbol)
        
        try:
            # Parse the JSON response
            result = json.loads(response)
            bias = result.get("bias", "neutral")
            confidence = float(result.get("confidence", 0.0))
            
            # Validate and normalize the response
            if bias not in ["bullish", "bearish", "neutral"]:
                bias = "neutral"
            confidence = max(0.0, min(1.0, confidence))  # Ensure 0.0 <= confidence <= 1.0
            
            # Cache the result with news-specific TTL
            _save_to_cache(cache_key, (bias, confidence), "news")
            
            return (bias, confidence)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse DeepSeek response as JSON: {response}")
            return ("neutral", 0.0)
            
    except Exception as e:
        logger.error(f"Error in news_bias: {e}")
        return ("neutral", 0.0)


def qa(question: str, context: Dict, offline: bool = False) -> str:
    """
    Answer a natural language question about trading data.
    
    Args:
        question: The question to answer
        context: Dictionary of context data including:
            signals: last_signal_dict
            positions: broker_state_dict
            cot: cot_dataframe.tail(4).to_dict()
            news: headlines_list
        offline: If True, return a fallback response without making an API call
            
    Returns:
        str: Answer to the question based on the provided context
    """
    if offline:
        return f"Offline mode: I would analyze {len(context.keys())} context elements to answer: '{question}'"
    
    # Create cache key
    cache_key = f"qa_{hash(question[:100])}_{hash(str(context)[:100])}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key, "chat")
    if cached_result:
        logger.info("Using cached QA response")
        return cached_result
    
    try:
        # Format the context as a string
        context_str = ""
        
        if "signals" in context and context["signals"]:
            context_str += "\nLatest Trading Signals:\n"
            context_str += json.dumps(context["signals"], indent=2)
        
        if "positions" in context and context["positions"]:
            context_str += "\nCurrent Positions:\n"
            context_str += json.dumps(context["positions"], indent=2)
        
        if "cot" in context and context["cot"]:
            context_str += "\nLatest COT Data:\n"
            context_str += str(context["cot"])
        
        if "news" in context and context["news"]:
            context_str += "\nRecent News Headlines:\n"
            for headline in context["news"]:
                context_str += f"- {headline}\n"
        
        prompt = f"""
        Based on the following trading context, please answer this question:
        
        Question: {question}
        
        Context:
        {context_str}
        
        Please provide a concise, accurate answer based only on the information provided.
        """
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant for a commodities trading bot. Answer questions based on the provided context."},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_chat(messages, temperature=0.3, max_tokens=500)
        
        # Cache the response
        _save_to_cache(cache_key, response, "chat")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in qa: {e}")
        return f"Sorry, I couldn't answer your question due to an error: {str(e)}"


def fetch_commodity_news(symbol: str, days: int = 3) -> List[str]:
    """
    Fetch recent news headlines for a specific commodity.
    
    Args:
        symbol: Trading symbol (e.g., 'XAUUSD')
        days: Number of days of news to retrieve
        
    Returns:
        List of news headlines
    """
    # Define symbol to keyword mapping
    symbol_keywords = {
        "XAUUSD": "gold OR \"precious metals\"",
        "XAGUSD": "silver OR \"precious metals\"",
        "WTICOUSD": "WTI OR crude OR oil",
        "BCOUSD": "brent OR crude OR oil",
        "NATGASUSD": "natural gas",
        "CORNUSD": "corn OR grain",
        "SOYBNUSD": "soybean OR grain",
        "WHEATUSD": "wheat OR grain"
    }
    
    if symbol not in symbol_keywords:
        return [f"No keyword mapping for {symbol}"]
    
    # Check cache first
    cache_key = f"news_{symbol}_{days}"
    cached_news = _get_from_cache(cache_key, "news")
    if cached_news:
        return cached_news
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Make API request
        params = {
            "q": symbol_keywords[symbol],
            "from": from_date,
            "to": to_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 15,
            "apiKey": NEWS_API_KEY
        }
        
        response = requests.get(NEWS_API_BASE, params=params)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"News API error: {data}")
            return [f"Error fetching news: {data.get('message', 'Unknown error')}"]
        
        # Extract headlines
        headlines = [article["title"] for article in data.get("articles", [])]
        
        # Cache the result with news-specific TTL
        _save_to_cache(cache_key, headlines, "news")
        
        return headlines
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return [f"Error fetching news: {str(e)}"]


def pattern_recognition(ohlc_data: pd.DataFrame, symbol: str, offline: bool = False) -> Dict:
    """
    Use DeepSeek to identify technical patterns in price data.
    
    Args:
        ohlc_data: DataFrame with OHLC price data
        symbol: Trading symbol (e.g., 'XAUUSD')
        offline: If True, return a fallback response without making an API call
        
    Returns:
        Dictionary with identified patterns and descriptions
    """
    if offline:
        return {
            "patterns": [],
            "support_levels": [],
            "resistance_levels": [],
            "summary": "Offline mode - no pattern recognition available."
        }
    
    # Create cache key based on the most recent data
    # Use only last N days to keep cache key manageable
    recent_data = ohlc_data.tail(20)
    # Cache key for this analysis
    price_snapshot = f"{ohlc_data.iloc[-5:]['close'].mean():.2f}"
    cache_key = f"pattern_{symbol}_{price_snapshot}"
    
    # Check cache with pattern-specific TTL
    cached_result = _get_from_cache(cache_key, "pattern")
    if cached_result and not offline:
        logger.info(f"Using cached pattern recognition for {symbol}")
        return cached_result
    
    try:
        # Format recent price data as text
        price_text = ""
        for _, row in recent_data.iterrows():
            date_str = row.name.strftime("%Y-%m-%d") if hasattr(row.name, 'strftime') else str(row.name)
            price_text += f"{date_str}: Open={row['open']:.2f}, High={row['high']:.2f}, Low={row['low']:.2f}, Close={row['close']:.2f}\n"
        
        # Calculate some basic indicators
        recent_data['sma_20'] = ohlc_data['close'].rolling(20).mean().tail(20)
        recent_data['sma_50'] = ohlc_data['close'].rolling(50).mean().tail(20)
        recent_data['rsi'] = calculate_rsi(ohlc_data['close'], 14).tail(20)
        
        # Add indicators to text
        indicators_text = ""
        latest = recent_data.iloc[-1]
        indicators_text += f"Latest indicators:\n"
        indicators_text += f"SMA20: {latest['sma_20']:.2f}\n"
        indicators_text += f"SMA50: {latest['sma_50']:.2f}\n"
        indicators_text += f"RSI(14): {latest['rsi']:.2f}\n"
        
        prompt = f"""
        Analyze the recent price action for {symbol} and identify any significant technical patterns.
        
        Recent price data (20 days):
        {price_text}
        
        {indicators_text}
        
        Please identify:
        1. Any chart patterns (e.g., head and shoulders, double top/bottom, triangles, flags, etc.)
        2. Key support levels
        3. Key resistance levels
        4. Brief interpretation of what these patterns suggest for future price action
        
        Structure your response as a JSON object with these keys:
        {{"patterns": [{{"name": "pattern name", "description": "brief description"}}], 
          "support_levels": [level1, level2, ...], 
          "resistance_levels": [level1, level2, ...], 
          "summary": "brief interpretation"}}
        """
        
        messages = [
            {"role": "system", "content": "You are an expert technical analyst specializing in chart pattern recognition. Provide objective, data-driven pattern identification in the format requested."},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_chat(messages, temperature=0.3, max_tokens=800)
        
        # Parse JSON from response
        try:
            # Find JSON object in response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                result = json.loads(json_str)
            else:
                # Fallback structure if JSON parsing fails
                result = {
                    "patterns": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "summary": response
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response with raw text
            result = {
                "patterns": [],
                "support_levels": [],
                "resistance_levels": [],
                "summary": response
            }
        
        # Cache the result with pattern-specific TTL
        _save_to_cache(cache_key, result, "pattern")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in pattern recognition: {e}")
        return {
            "patterns": [],
            "support_levels": [],
            "resistance_levels": [],
            "summary": f"Error in pattern recognition: {str(e)}"
        }


def portfolio_optimization(positions: List[Dict], risk_profile: str = "moderate", offline: bool = False) -> Dict:
    """
    Use DeepSeek to optimize portfolio allocation based on current positions and risk profile.
    
    Args:
        positions: List of current position dictionaries
        risk_profile: Risk tolerance ("conservative", "moderate", "aggressive")
        offline: If True, return a fallback response without making an API call
        
    Returns:
        Dictionary with optimization suggestions
    """
    if offline:
        return {
            "recommendations": {
                "allocation_changes": [],
                "risk_management": []
            },
            "rationale": "Offline mode - no portfolio optimization available."
        }
    
    # Cache key for this optimization
    positions_hash = hash(str(positions)[:200])  # Limit size for hash
    cache_key = f"portfolio_opt_{positions_hash}_{risk_profile}"
    
    # Check cache with portfolio-specific TTL
    cached_result = _get_from_cache(cache_key, "portfolio")
    if cached_result and not offline:
        logger.info("Using cached portfolio optimization")
        return cached_result
    
    try:
        # Format current positions
        positions_text = json.dumps(positions, indent=2)
        
        # Define risk profiles
        risk_profiles = {
            "conservative": "Low risk tolerance. Prioritize capital preservation over growth. Maintain tight stop losses and conservative position sizing.",
            "moderate": "Balanced approach. Willing to accept moderate risk for moderate returns. Reasonable stop losses and standard position sizing.",
            "aggressive": "High risk tolerance. Seeking higher returns and willing to accept larger drawdowns. May use wider stop losses and larger position sizes."
        }
        
        risk_description = risk_profiles.get(risk_profile, risk_profiles["moderate"])
        
        prompt = f"""
        Please analyze the current trading portfolio and provide optimization suggestions based on a {risk_profile.upper()} risk profile.
        
        Risk Profile: {risk_description}
        
        Current Positions:
        {positions_text}
        
        Please provide:
        1. Recommendations for allocation changes (increase, decrease, or maintain positions)
        2. Risk management suggestions (stop loss adjustments, position sizing changes, etc.)
        3. Rationale for your recommendations
        
        Structure your response as a JSON object with these keys:
        {{"recommendations": {{"allocation_changes": [{{"symbol": "SYMBOL", "action": "increase/decrease/maintain", "reasoning": "..."}}, ...], "risk_management": ["suggestion1", "suggestion2", ...]}}, "rationale": "overall rationale"}}
        """
        
        messages = [
            {"role": "system", "content": "You are a portfolio manager specializing in risk management and asset allocation. Provide objective, data-driven portfolio recommendations in the format requested."},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_chat(messages, temperature=0.3, max_tokens=1000)
        
        # Parse JSON from response
        try:
            # Find JSON object in response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                result = json.loads(json_str)
            else:
                # Fallback structure if JSON parsing fails
                result = {
                    "recommendations": {
                        "allocation_changes": [],
                        "risk_management": []
                    },
                    "rationale": response
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response with raw text
            result = {
                "recommendations": {
                    "allocation_changes": [],
                    "risk_management": []
                },
                "rationale": response
            }
        
        # Cache the result with portfolio-specific TTL
        _save_to_cache(cache_key, result, "portfolio")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}")
        return {
            "recommendations": {
                "allocation_changes": [],
                "risk_management": []
            },
            "rationale": f"Error in portfolio optimization: {str(e)}"
        }


def scenario_analysis(portfolio: Dict, scenarios: List[str] = None, offline: bool = False) -> Dict:
    """
    Use DeepSeek to analyze how the portfolio might perform under different market scenarios.
    
    Args:
        portfolio: Dictionary with current positions and account information
        scenarios: List of specific scenarios to analyze (optional)
        offline: If True, return a fallback response without making an API call
        
    Returns:
        Dictionary with scenario analysis results
    """
    if offline:
        return {
            "scenarios": [],
            "summary": "Offline mode - no scenario analysis available."
        }
    
    # Cache key for this analysis
    portfolio_hash = hash(str(portfolio)[:200])  # Limit size for hash
    scenarios_hash = hash(str(scenarios)[:100])
    cache_key = f"scenario_{portfolio_hash}_{scenarios_hash}"
    
    # Check cache with scenario-specific TTL
    cached_result = _get_from_cache(cache_key, "scenario")
    if cached_result and not offline:
        logger.info("Using cached scenario analysis")
        return cached_result
    
    try:
        # Format portfolio
        portfolio_text = json.dumps(portfolio, indent=2)
        
        # Default scenarios if none provided
        default_scenarios = [
            "Equity market sell-off (-5% major indices)",
            "US Dollar strengthening (+2% DXY)",
            "Inflation data higher than expected",
            "Central bank hawkish surprise",
            "Geopolitical tensions escalation"
        ]
        
        scenarios_to_analyze = scenarios if scenarios else default_scenarios
        scenarios_text = "\n".join([f"- {s}" for s in scenarios_to_analyze])
        
        prompt = f"""
        Please analyze how the current portfolio would likely perform under the following market scenarios.
        
        Current Portfolio:
        {portfolio_text}
        
        Scenarios to analyze:
        {scenarios_text}
        
        For each scenario, provide:
        1. Likely impact on each position (positive, negative, or neutral)
        2. Estimated portfolio impact (percentage change)
        3. Suggested hedging strategies or position adjustments
        
        Structure your response as a JSON object with these keys:
        {{"scenarios": [{{"name": "scenario name", "impacts": [{{"symbol": "SYMBOL", "impact": "positive/negative/neutral", "magnitude": "high/medium/low"}}], "portfolio_impact": "estimated percentage", "hedge_suggestions": ["suggestion1", "suggestion2"]}}], "summary": "overall summary"}}
        """
        
        messages = [
            {"role": "system", "content": "You are a risk analyst specializing in scenario analysis and stress testing. Provide objective, data-driven scenario analysis in the format requested."},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_chat(messages, temperature=0.3, max_tokens=1500)
        
        # Parse JSON from response
        try:
            # Find JSON object in response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                result = json.loads(json_str)
            else:
                # Fallback structure if JSON parsing fails
                result = {
                    "scenarios": [],
                    "summary": response
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response with raw text
            result = {
                "scenarios": [],
                "summary": response
            }
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in scenario analysis: {e}")
        return {
            "scenarios": [],
            "summary": f"Error in scenario analysis: {str(e)}"
        }


def calculate_rsi(series, period=14):
    """Calculate the Relative Strength Index (RSI) for a price series."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_cache_stats():
    """Get statistics about the cache usage.
    
    Returns:
        Dict with cache statistics
    """
    stats = {
        "memory_items": len(MEMORY_CACHE),
        "memory_limit": MAX_MEMORY_CACHE_ITEMS,
        "disk_usage_mb": 0,
        "disk_limit_mb": MAX_DISK_CACHE_SIZE_MB,
        "compression_enabled": COMPRESSION_ENABLED,
        "compression_level": COMPRESSION_LEVEL,
        "by_type": {}
    }
    
    # Usa il gestore delle chiavi per generare statistiche dettagliate
    key_stats = cache_key_manager.generate_key_stats()
    
    # Calcola statistiche globali
    total_size = 0
    total_count = 0
    
    for cache_type, type_stats in key_stats.items():
        total_size += type_stats["size_kb"] * 1024  # Converti KB in bytes
        total_count += type_stats["count"]
    
    stats["disk_usage_mb"] = total_size / (1024 * 1024)
    stats["total_cache_files"] = total_count
    stats["by_type"] = key_stats
    
    return stats


def self_test():
    """Run self-test to validate the module functionality."""
    print("Running DeepSeek Utils self-test...")
    
    # Test cache key manager
    print("\nTesting cache key manager:")
    test_queries = [
        "Una query normale per il test",
        "QUERY CON MAIUSCOLE e spazi   multipli e caratteri speciali !@#$%^",
        "Query molto lunga " + "con ripetizioni " * 20
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\nOriginal query {i+1}: {query[:50]}..." if len(query) > 50 else f"\nOriginal query {i+1}: {query}")
        
        # Test normalizzazione
        normalized = cache_key_manager.normalize_key(query)
        print(f"Normalized: {normalized[:50]}..." if len(normalized) > 50 else f"Normalized: {normalized}")
        
        # Test creazione chiave per DeepSeek
        key = cache_key_manager.create_query_key(query, "deepseek-chat", {"temperature": 0.7})
        print(f"Cache key: {key[:50]}..." if len(key) > 50 else f"Cache key: {key}")
        
        # Test percorso file
        path = cache_key_manager.get_cache_path(key, "chat")
        print(f"Cache path: {path}")
    
    # Test cache compression
    print("\nTesting cache compression:")
    test_data = {
        "large_text": "A" * 5000,  # Create data above compression threshold
        "sample_values": list(range(100))
    }
    cache_key = "compression_test"
    
    # Save to cache
    _save_to_cache(cache_key, test_data, "test")
    
    # Retrieve from cache
    retrieved_data = _get_from_cache(cache_key, "test")
    
    if retrieved_data:
        cache_path = _get_cache_path(cache_key, "test")
        compressed_size = cache_path.stat().st_size if cache_path.exists() else 0
        estimated_raw_size = len(json.dumps(test_data).encode('utf-8'))
        compression_ratio = estimated_raw_size / compressed_size if compressed_size > 0 else 0
        print(f"Cache compression test successful! Ratio: {compression_ratio:.2f}x")
        print(f"Raw size: {estimated_raw_size} bytes, Compressed: {compressed_size} bytes")
    else:
        print("Cache test failed!")
        
    # Test integrazione completa
    print("\nTesting full integration:")
    test_prompt = "What is the current market outlook for gold?"
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant for trading."},
        {"role": "user", "content": test_prompt}
    ]
    offline_response = deepseek_chat(test_messages, offline=True, cache_type="test")
    if offline_response is None or offline_response.startswith("Sorry"):
        print("Cache miss - not found in cache (expected for first run)")
        # Salva un test nella cache
        test_key = cache_key_manager.create_query_key(test_prompt, "deepseek-chat", {"temperature": 0.3})
        _save_to_cache(test_key, "This is a test response for caching.", "test")
        
        # Prova nuovamente
        offline_response = deepseek_chat(test_messages, offline=True, cache_type="test")
        if offline_response and not offline_response.startswith("Sorry"):
            print("Cache hit after manual save - integration successful!")
        else:
            print("Cache integration test failed!")
    else:
        print("Cache hit - found in cache!")
        print(f"Response: {offline_response[:50]}..." if len(offline_response) > 50 else f"Response: {offline_response}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepSeek Utils for OpenMT4TradingBot")
    parser.add_argument("--selftest", action="store_true", help="Run self-test")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode")
    parser.add_argument("--news", type=str, help="Fetch news for symbol (e.g., XAUUSD)")
    parser.add_argument("--analyze", type=str, help="Run market analysis for symbol")
    parser.add_argument("--compress", type=int, choices=range(0, 10), default=COMPRESSION_LEVEL, 
                      help="Set compression level (0-9, where 9 is max compression)")
    parser.add_argument("--nocompress", action="store_true", help="Disable compression")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    
    args = parser.parse_args()
    
    # Handle compression settings
    if args.nocompress:
        COMPRESSION_ENABLED = False
        print("Cache compression disabled")
    else:
        COMPRESSION_LEVEL = args.compress
        print(f"Cache compression level set to {COMPRESSION_LEVEL}")
        
    # Mostra statistiche della cache se richiesto
    if args.cache_stats:
        print("\nCache Statistics:")
        stats = get_cache_stats()
        print(f"Memory cache: {stats['memory_items']}/{stats['memory_limit']} items")
        print(f"Disk usage: {stats['disk_usage_mb']:.2f} MB / {stats['disk_limit_mb']} MB limit")
        print(f"Compression: {'Enabled' if stats['compression_enabled'] else 'Disabled'} (level {stats['compression_level']})")
        
        print("\nBy cache type:")
        for cache_type, type_stats in stats['by_type'].items():
            print(f"  {cache_type}: {type_stats['count']} files, {type_stats['size_kb']:.2f} KB total")
    
    if args.news:
        print(f"Fetching news for {args.news}...")
        headlines = fetch_commodity_news(args.news, days=5)
        for headline in headlines:
            print(f"- {headline}")
    
    elif args.analyze:
        print(f"Analyzing {args.analyze}...")
        # Demo with mock data
        mock_data = pd.DataFrame({
            'open': [1800, 1805, 1810, 1815, 1820],
            'high': [1810, 1815, 1820, 1825, 1830],
            'low': [1790, 1795, 1800, 1805, 1810],
            'close': [1805, 1810, 1815, 1820, 1825]
        }, index=pd.date_range(end=datetime.now(), periods=5))
        
        results = analyze_market_factors(args.analyze, mock_data, offline=args.offline)
        print(json.dumps(results, indent=2))
    
    elif args.selftest:
        self_test()
