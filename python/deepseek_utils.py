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
import pickle
import logging
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deepseek_utils")

# Constants
CACHE_DIR = Path("cache")
CACHE_TTL = 300  # Cache time-to-live in seconds
DEFAULT_MODEL = "deepseek-chat"  # or "deepseek-reasoner"

# News API settings
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_BASE = "https://newsapi.org/v2/everything"
NEWS_CACHE_TTL = 3600  # 1 hour cache for news

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)

# Load API key and base URL from environment variables
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MODEL = os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)


def _get_cache_path(cache_key: str) -> Path:
    """Get cache file path for a given key."""
    # Use a hash of the cache_key to avoid file system issues
    hashed_key = str(hash(cache_key))
    return CACHE_DIR / f"{hashed_key}.pickle"


def _get_from_cache(cache_key: str) -> Optional[Any]:
    """Retrieve data from cache if it exists and is not expired."""
    cache_path = _get_cache_path(cache_key)
    
    if not cache_path.exists():
        return None
        
    try:
        with open(cache_path, 'rb') as f:
            cached_data = pickle.load(f)
            
        # Check if cache has expired
        if time.time() - cached_data['timestamp'] > CACHE_TTL:
            return None
            
        return cached_data['data']
    except Exception as e:
        logger.warning(f"Failed to read from cache: {e}")
        return None


def _save_to_cache(cache_key: str, data: Any) -> bool:
    """Save data to cache with current timestamp."""
    cache_path = _get_cache_path(cache_key)
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump({
                'timestamp': time.time(),
                'data': data
            }, f)
        return True
    except Exception as e:
        logger.warning(f"Failed to write to cache: {e}")
        return False


def deepseek_chat(messages: List[Dict], model: str = None, temperature: float = 0.7, 
                 max_tokens: int = 1000, offline: bool = False) -> str:
    """
    Send a chat request to the DeepSeek API.
    
    Args:
        messages: List of message dictionaries in OpenAI format
                 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        model: Model name to use
        temperature: Temperature parameter for generation
        max_tokens: Maximum tokens to generate
        offline: If True, return a fallback response without making an API call
        
    Returns:
        str: Response from the DeepSeek API
    """
    if offline:
        return "DeepSeek API is in offline mode. This is a fallback response."
        
    if not API_KEY:
        return "DeepSeek API key not configured. Set the DEEPSEEK_API_KEY environment variable."
    
    # Create cache key from the request parameters
    cache_key = str(hash(str(messages) + str(model) + str(temperature) + str(max_tokens)))
    
    # Check cache first
    cached_response = _get_from_cache(cache_key)
    if cached_response:
        logger.info("Using cached DeepSeek response")
        return cached_response
    
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
    
    # Create cache key
    cache_key = f"news_bias_{symbol}_{hash(str(headlines))}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
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
        
        response = deepseek_chat(messages, temperature=0.1)
        
        try:
            # Parse the JSON response
            result = json.loads(response)
            bias = result.get("bias", "neutral")
            confidence = float(result.get("confidence", 0.0))
            
            # Validate and normalize the response
            if bias not in ["bullish", "bearish", "neutral"]:
                bias = "neutral"
            confidence = max(0.0, min(1.0, confidence))  # Ensure 0.0 <= confidence <= 1.0
            
            # Cache the result
            _save_to_cache(cache_key, (bias, confidence))
            
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
    cache_key = f"qa_{hash(question)}_{hash(str(context))}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
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
        _save_to_cache(cache_key, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in qa: {e}")
        return f"Sorry, I couldn't answer your question due to an error: {str(e)}"


# Self-test function
def self_test():
    """Run self-test to validate the module functionality."""
    print("Running DeepSeek Utils self-test...")
    
    # Test news_bias
    test_headlines = [
        "Gold prices surge to 3-month high as inflation fears mount",
        "Fed signals potential rate hikes, pressuring precious metals",
        "Analysts predict continued strength in commodity markets"
    ]
    
    print("\nTesting news_bias with offline mode:")
    bias, confidence = news_bias("XAUUSD", test_headlines, offline=True)
    print(f"Bias: {bias}, Confidence: {confidence}")
    
    # Test Q&A
    test_context = {
        "signals": {
            "XAUUSD": {
                "direction": "BUY",
                "entry": 2350.25,
                "sl": 2320.75,
                "tp": 2405.50,
                "timestamp": int(time.time())
            }
        },
        "positions": {
            "positions": [
                {
                    "symbol": "XAUUSD",
                    "type": "BUY",
                    "lots": 0.1,
                    "openPrice": 2350.25,
                    "sl": 2320.75,
                    "tp": 2405.50,
                    "profit": 15.25
                }
            ],
            "account": {
                "balance": 10000.00,
                "equity": 10015.25
            }
        },
        "news": test_headlines
    }
    
    test_questions = [
        "What is our current position in gold?",
        "Why did we enter the trade on gold?",
        "What's our current profit on all positions?"
    ]
    
    print("\nTesting QA with offline mode:")
    for question in test_questions:
        answer = qa(question, test_context, offline=True)
        print(f"Q: {question}")
        print(f"A: {answer}")
        print()
    
    print("Self-test completed.")


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
    cached_news = _get_from_cache(cache_key)
    if cached_news:
        return cached_news
    
    # If no NEWS_API_KEY, return mock data
    if not NEWS_API_KEY:
        mock_headlines = [
            f"Analysts predict higher {symbol.replace('USD', '')} prices amid market uncertainty",
            f"Supply constraints could impact {symbol.replace('USD', '')} in coming months",
            f"Economic data shows mixed signals for {symbol.replace('USD', '')} demand"
        ]
        _save_to_cache(cache_key, mock_headlines)
        return mock_headlines
    
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
        
        # Cache the results
        _save_to_cache(cache_key, headlines)
        
        return headlines
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return [f"Error fetching news: {str(e)}"]


def analyze_market_factors(symbol: str, ohlc_data: pd.DataFrame = None, context: Dict = None, offline: bool = False) -> Dict:
    """
    Perform a multi-factor analysis of a commodity using DeepSeek AI.
    
    Args:
        symbol: Trading symbol (e.g., 'XAUUSD')
        ohlc_data: DataFrame with OHLC price data (optional)
        context: Additional context data (COT, seasonal info, etc.)
        offline: If True, return a fallback response without making an API call
        
    Returns:
        Dictionary with analysis results for different timeframes and factors
    """
    if offline:
        return {
            "timeframes": {
                "short_term": "neutral",
                "medium_term": "neutral",
                "long_term": "neutral"
            },
            "factors": {
                "supply_demand": "balanced",
                "macro_influence": "neutral",
                "technical_outlook": "neutral"
            },
            "summary": "Offline mode - no real analysis available."
        }
    
    # Create cache key
    data_hash = ""
    if ohlc_data is not None:
        # Use last 5 rows of data to create a hash
        data_hash = str(hash(str(ohlc_data.tail(5).values.tolist())))
    
    context_hash = str(hash(str(context))) if context else ""
    cache_key = f"analysis_{symbol}_{data_hash}_{context_hash}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    try:
        # Prepare data for analysis
        market_context = ""
        
        # Add OHLC data if available
        if ohlc_data is not None:
            # Get basic stats
            recent_data = ohlc_data.tail(20)
            last_close = recent_data['close'].iloc[-1]
            prev_close = recent_data['close'].iloc[-2]
            price_change = (last_close - prev_close) / prev_close * 100
            price_change_str = f"{price_change:.2f}%"
            
            # Calculate some basic technical indicators
            sma_20 = recent_data['close'].mean()
            high_52w = ohlc_data['high'].tail(252).max()
            low_52w = ohlc_data['low'].tail(252).min()
            
            market_context += f"""
            Recent price action for {symbol}:            
            - Last close: {last_close}
            - Daily change: {price_change_str}
            - 20-day average: {sma_20:.2f}
            - 52-week high: {high_52w}
            - 52-week low: {low_52w}
            """
        
        # Add context data if available
        if context:
            if "cot" in context and context["cot"]:
                market_context += f"\nCOT Data:\n{str(context['cot'])}\n"
            
            if "seasonal" in context and context["seasonal"]:
                market_context += f"\nSeasonal Tendencies:\n{str(context['seasonal'])}\n"
                
        # Get recent news
        headlines = fetch_commodity_news(symbol)
        if headlines:
            market_context += "\nRecent News Headlines:\n"
            for headline in headlines:
                market_context += f"- {headline}\n"
        
        prompt = f"""
        Please provide a comprehensive multi-factor analysis for {symbol} based on the information below.
        
        {market_context}
        
        For your analysis, include:
        
        1. Timeframe outlook:
           - Short-term (1-5 days): bullish, bearish, or neutral with reasoning
           - Medium-term (1-4 weeks): bullish, bearish, or neutral with reasoning
           - Long-term (1-6 months): bullish, bearish, or neutral with reasoning
        
        2. Factor analysis:
           - Supply/Demand dynamics: surplus, deficit, or balanced
           - Macroeconomic influence: supportive, challenging, or neutral
           - Technical price outlook: bullish, bearish, or neutral
        
        3. Brief summary of overall outlook (2-3 sentences)
        
        Structure your response as a JSON object with these keys:
        {{"timeframes": {{...}}, "factors": {{...}}, "summary": "..."}}
        """
        
        messages = [
            {"role": "system", "content": "You are a commodity market analyst with expertise in fundamental, technical, and macro analysis. Provide objective, data-driven insights in the format requested."},
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
                    "timeframes": {
                        "short_term": "unknown",
                        "medium_term": "unknown",
                        "long_term": "unknown"
                    },
                    "factors": {
                        "supply_demand": "unknown",
                        "macro_influence": "unknown",
                        "technical_outlook": "unknown"
                    },
                    "summary": response
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured response with raw text
            result = {
                "timeframes": {
                    "short_term": "unknown",
                    "medium_term": "unknown",
                    "long_term": "unknown"
                },
                "factors": {
                    "supply_demand": "unknown",
                    "macro_influence": "unknown",
                    "technical_outlook": "unknown"
                },
                "summary": response
            }
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in market factor analysis: {e}")
        return {
            "timeframes": {
                "short_term": "error",
                "medium_term": "error",
                "long_term": "error"
            },
            "factors": {
                "supply_demand": "error",
                "macro_influence": "error",
                "technical_outlook": "error"
            },
            "summary": f"Error analyzing market factors: {str(e)}"
        }


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
    data_hash = str(hash(str(recent_data.values.tolist())))
    cache_key = f"patterns_{symbol}_{data_hash}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
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
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
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
    
    # Create cache key
    positions_hash = str(hash(str(positions)))
    cache_key = f"portfolio_{positions_hash}_{risk_profile}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
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
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
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
    
    # Create cache key
    portfolio_hash = str(hash(str(portfolio)))
    scenarios_hash = str(hash(str(scenarios))) if scenarios else ""
    cache_key = f"scenarios_{portfolio_hash}_{scenarios_hash}"
    
    # Check cache
    cached_result = _get_from_cache(cache_key)
    if cached_result:
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepSeek Utils for OpenMT4TradingBot")
    parser.add_argument("--selftest", action="store_true", help="Run self-test")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode")
    parser.add_argument("--news", type=str, help="Fetch news for symbol (e.g., XAUUSD)")
    parser.add_argument("--analyze", type=str, help="Run market analysis for symbol")
    
    args = parser.parse_args()
    
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
