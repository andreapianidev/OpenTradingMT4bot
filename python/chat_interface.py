#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chat interface for OpenMT4TradingBot.

This module provides a web API or CLI interface to interact with 
the trading bot using natural language queries via DeepSeek.

MIT License

Copyright (c) 2025 Immaginet Srl
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime

# Try importing FastAPI related modules
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel
    
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Try importing rich for CLI prettification
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

# Try importing DeepSeek utilities
try:
    from deepseek_utils import qa, analyze_market_factors, pattern_recognition, portfolio_optimization, scenario_analysis, fetch_commodity_news
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chat_interface.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("chat_interface")

# Constants
MT4_FILES_PATH = os.path.expanduser("~/AppData/Roaming/MetaTrader 4/MQL4/Files/OpenMT4TradingBot")
DATA_PATH = "../data"
CONTEXT_REFRESH_SECONDS = 60
CONVERSATION_HISTORY_MAX = 10  # Maximum number of conversation exchanges to keep


class Context:
    """Context manager for trading data."""
    
    def __init__(self, mt4_path: str = MT4_FILES_PATH, data_path: str = DATA_PATH):
        """
        Initialize context manager.
        
        Args:
            mt4_path: Path to MT4 Files directory
            data_path: Path to data directory
        """
        self.mt4_path = Path(mt4_path)
        self.data_path = Path(data_path)
        self.last_update = 0
        self.context = {}
        self.refresh()
        
    def refresh(self) -> bool:
        """Refresh the context data from files."""
        current_time = time.time()
        
        # Only refresh if enough time has passed
        if current_time - self.last_update < CONTEXT_REFRESH_SECONDS:
            return False
            
        try:
            # Load signals
            signal_file = self.mt4_path / "signal.json"
            if signal_file.exists():
                with open(signal_file, 'r') as f:
                    self.context['signals'] = json.load(f)
            
            # Load positions
            positions_file = self.mt4_path / "positions.json"
            if positions_file.exists():
                with open(positions_file, 'r') as f:
                    self.context['positions'] = json.load(f)
            
            # Load COT data
            cot_file = self.data_path / "cot.csv"
            if cot_file.exists():
                try:
                    cot_df = pd.read_csv(cot_file)
                    # Get last 4 rows for each symbol
                    self.context['cot'] = {}
                    for symbol in cot_df['Symbol'].unique():
                        symbol_df = cot_df[cot_df['Symbol'] == symbol].tail(4)
                        self.context['cot'][symbol] = symbol_df.to_dict('records')
                except Exception as e:
                    logger.error(f"Error loading COT data: {e}")
            
            # Load news (placeholder - would come from a news API in production)
            self.context['news'] = []
            
            self.last_update = current_time
            logger.info("Context refreshed")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing context: {e}")
            return False
    
    def get(self) -> Dict:
        """Get the current context."""
        self.refresh()
        return self.context


class ConversationManager:
    """Manager for conversation history and context."""
    
    def __init__(self, context_manager):
        """
        Initialize conversation manager.
        
        Args:
            context_manager: Context manager instance
        """
        self.context_manager = context_manager
        self.history = []
        self.last_symbol = None  # Track the last symbol discussed
        
    def add_exchange(self, question, answer):
        """
        Add a question-answer exchange to the history.
        
        Args:
            question: User's question
            answer: System's answer
        """
        self.history.append({"question": question, "answer": answer, "timestamp": time.time()})
        
        # Keep only the last N exchanges
        if len(self.history) > CONVERSATION_HISTORY_MAX:
            self.history = self.history[-CONVERSATION_HISTORY_MAX:]
            
    def get_history_context(self):
        """
        Get the conversation history formatted for context.
        
        Returns:
            str: Formatted conversation history
        """
        if not self.history:
            return ""
            
        history_text = "\nRecent conversation history:\n"
        for i, exchange in enumerate(self.history[-3:]):  # Only include last 3 exchanges
            history_text += f"User: {exchange['question']}\n"
            history_text += f"Assistant: {exchange['answer']}\n\n"
            
        return history_text
    
    def detect_symbol(self, question):
        """
        Detect which trading symbol the question is about.
        
        Args:
            question: User's question
            
        Returns:
            str or None: Detected symbol or None
        """
        # List of supported symbols
        symbols = ["XAUUSD", "XAGUSD", "WTICOUSD", "BCOUSD", "NATGASUSD", "CORNUSD", "SOYBNUSD", "WHEATUSD"]
        
        # Also check common names
        symbol_aliases = {
            "gold": "XAUUSD", 
            "silver": "XAGUSD", 
            "wti": "WTICOUSD", 
            "crude": "WTICOUSD",
            "oil": "WTICOUSD", 
            "brent": "BCOUSD",
            "natural gas": "NATGASUSD", 
            "natgas": "NATGASUSD",
            "corn": "CORNUSD", 
            "soybean": "SOYBNUSD", 
            "soybeans": "SOYBNUSD", 
            "wheat": "WHEATUSD"
        }
        
        # Check for exact symbol matches
        for symbol in symbols:
            if symbol in question.upper():
                self.last_symbol = symbol
                return symbol
                
        # Check for aliases
        for alias, symbol in symbol_aliases.items():
            if alias.lower() in question.lower():
                self.last_symbol = symbol
                return symbol
                
        # If no symbol found but we have a last symbol from context, use that
        return self.last_symbol
    
    def parse_command(self, question):
        """
        Parse special commands in the question.
        
        Args:
            question: User's question
            
        Returns:
            tuple: (command_type, parameters) or (None, None) if not a command
        """
        # Check for command format: /command args
        if not question.startswith("/"):
            return None, None
            
        parts = question.split(" ", 1)
        command = parts[0][1:].lower()  # Remove the / and convert to lowercase
        args = parts[1] if len(parts) > 1 else ""
        
        # List of supported commands
        if command in ["analizza", "analyze"]:
            symbol = args.strip().upper() if args else self.detect_symbol(question)
            return "analyze", {"symbol": symbol}
            
        elif command in ["pattern", "patterns"]:
            symbol = args.strip().upper() if args else self.detect_symbol(question)
            return "patterns", {"symbol": symbol}
            
        elif command in ["rischio", "risk"]:
            return "risk", {}
            
        elif command in ["ottimizza", "optimize"]:
            return "optimize", {}
            
        elif command in ["correlazioni", "correlations"]:
            return "correlations", {}
            
        elif command in ["news", "notizie"]:
            symbol = args.strip().upper() if args else self.detect_symbol(question)
            return "news", {"symbol": symbol}
            
        elif command in ["scenario", "scenarios"]:
            return "scenarios", {}
            
        elif command in ["help", "aiuto"]:
            return "help", {}
            
        # Not a recognized command
        return None, None


# Create managers
context_manager = Context()
conversation_manager = ConversationManager(context_manager)


def ask_question(question: str, refresh: bool = False) -> str:
    """
    Ask a question using DeepSeek.
    
    Args:
        question: Question to ask
        refresh: Whether to force context refresh
        
    Returns:
        str: Answer to the question
    """
    # Check if DeepSeek is available
    if not DEEPSEEK_AVAILABLE:
        return "DeepSeek is not available. Please install the required dependencies."
        
    # Refresh context if requested
    if refresh:
        context_manager.refresh()
        
    # Check for special commands
    command, params = conversation_manager.parse_command(question)
    
    # Execute command if detected
    answer = ""
    if command:
        try:
            if command == "analyze":
                symbol = params.get("symbol")
                if not symbol:
                    return "Per favore, specifica un simbolo da analizzare."
                    
                logger.info(f"Analyzing market factors for {symbol}...")
                context = context_manager.get()
                price_data = context.get("prices", {}).get(symbol, {})
                cot_data = context.get("cot", {}).get(symbol, [])
                
                result = analyze_market_factors(
                    symbol=symbol,
                    price_data=price_data,
                    cot_data=cot_data,
                    offline=False
                )
                
                answer = f"## Analisi di mercato per {symbol}\n\n"
                answer += json.dumps(result, indent=2)
                
            elif command == "patterns":
                symbol = params.get("symbol")
                if not symbol:
                    return "Per favore, specifica un simbolo per l'analisi dei pattern."
                    
                logger.info(f"Recognizing patterns for {symbol}...")
                context = context_manager.get()
                price_data = context.get("prices", {}).get(symbol, {})
                
                result = pattern_recognition(
                    symbol=symbol, 
                    price_data=price_data,
                    offline=False
                )
                
                answer = f"## Pattern riconosciuti per {symbol}\n\n"
                answer += json.dumps(result, indent=2)
                
            elif command == "optimize":
                logger.info("Optimizing portfolio...")
                context = context_manager.get()
                positions = context.get("positions", [])
                
                result = portfolio_optimization(
                    current_positions=positions,
                    risk_profile="moderate",  # Default
                    offline=False
                )
                
                answer = "## Ottimizzazione del portafoglio\n\n"
                answer += json.dumps(result, indent=2)
                
            elif command == "scenarios":
                logger.info("Running scenario analysis...")
                context = context_manager.get()
                positions = context.get("positions", [])
                
                result = scenario_analysis(
                    current_positions=positions,
                    offline=False
                )
                
                answer = "## Analisi degli scenari\n\n"
                answer += json.dumps(result, indent=2)
                
            elif command == "news":
                symbol = params.get("symbol")
                if not symbol:
                    return "Per favore, specifica un simbolo per le notizie."
                    
                logger.info(f"Fetching news for {symbol}...")
                news = fetch_commodity_news(symbol, max_results=5, offline=False)
                
                answer = f"## Ultime notizie per {symbol}\n\n"
                if news and len(news) > 0:
                    for item in news:
                        answer += f"- **{item['title']}** ({item['date']})\n  {item['url']}\n\n"
                else:
                    answer += "Nessuna notizia trovata."
                
            elif command == "help":
                answer = """## Comandi disponibili:

/analyze [symbol] - Analizza i fattori di mercato per un simbolo
/patterns [symbol] - Riconosce i pattern tecnici per un simbolo
/optimize - Ottimizza il portafoglio corrente
/scenarios - Esegue un'analisi di scenario per il portafoglio
/news [symbol] - Mostra le ultime notizie per un simbolo
/risk - Mostra il profilo di rischio corrente

Puoi anche fare domande in linguaggio naturale come:
"Come sta andando l'oro oggi?"
"Quali sono le prospettive per il petrolio a lungo termine?"
"Dovrei aumentare l'esposizione sul gas naturale?"
"""
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            answer = f"Si è verificato un errore durante l'esecuzione del comando: {str(e)}"
    
    # If not a command or command failed, use QA
    if not answer:
        # Get current context with conversation history
        context = context_manager.get()
        
        # Add conversation history to context
        history_context = conversation_manager.get_history_context()
        if history_context and isinstance(context, dict):
            context["conversation_history"] = history_context
        
        # Call DeepSeek QA
        answer = qa(question, context, offline=False)
    
    # Add to conversation history
    conversation_manager.add_exchange(question, answer)
    
    return answer


# FastAPI app (if available)
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="OpenMT4TradingBot Chat API",
        description="API for interacting with the trading bot using natural language",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API models
    class QuestionRequest(BaseModel):
        question: str
        force_refresh: bool = False
    
    class ConversationResponse(BaseModel):
        answer: str
        conversation_id: str
    
    class ConversationHistoryResponse(BaseModel):
        history: list
        
    @app.post("/ask")
    async def api_ask(request: QuestionRequest):
        """API endpoint for asking questions."""
        try:
            answer = ask_question(request.question, refresh=request.force_refresh)
            return {
                "answer": answer, 
                "conversation_id": "current",  # For now we only support one conversation
                "timestamp": int(time.time())
            }
        except Exception as e:
            logger.error(f"Error in /ask endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/context")
    async def api_context():
        """API endpoint for getting the current context."""
        try:
            return context_manager.get()
        except Exception as e:
            logger.error(f"Error in /context endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.get("/conversation")
    async def api_conversation():
        """API endpoint for getting the conversation history."""
        try:
            return {"history": conversation_manager.history}
        except Exception as e:
            logger.error(f"Error in /conversation endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.post("/command/{command}")
    async def api_command(command: str, request: dict = {}):
        """API endpoint for executing specific commands."""
        try:
            # Create a synthetic question in command format
            cmd_question = f"/{command}"
            if "symbol" in request and request["symbol"]:
                cmd_question += f" {request['symbol']}"
                
            answer = ask_question(cmd_question, refresh=True)
            return {"result": answer}
        except Exception as e:
            logger.error(f"Error in /command endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def run_cli():
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description='OpenMT4TradingBot Chat Interface')
    parser.add_argument('question', nargs='?', type=str, help='Question to ask')
    parser.add_argument('--refresh', action='store_true', help='Force context refresh')
    parser.add_argument('--server', action='store_true', help='Run as web server')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    
    # Add command-specific arguments
    parser.add_argument('--analyze', metavar='SYMBOL', help='Analyze market factors for a symbol')
    parser.add_argument('--patterns', metavar='SYMBOL', help='Recognize patterns for a symbol')
    parser.add_argument('--news', metavar='SYMBOL', help='Fetch news for a symbol')
    parser.add_argument('--optimize', action='store_true', help='Optimize portfolio')
    parser.add_argument('--scenarios', action='store_true', help='Run scenario analysis')
    
    args = parser.parse_args()
    
    # If server mode is requested
    if args.server:
        if not FASTAPI_AVAILABLE:
            print("Error: FastAPI and uvicorn are required to run in server mode.")
            print("Please install with: pip install fastapi uvicorn")
            return
            
        print(f"Starting web server on port {args.port}...")
        uvicorn.run("chat_interface:app", host="0.0.0.0", port=args.port, reload=False)
        return
    
    # Check for command-line commands
    if args.analyze:
        answer = ask_question(f"/analyze {args.analyze}", refresh=args.refresh)
        _print_answer(answer)
        return
        
    if args.patterns:
        answer = ask_question(f"/patterns {args.patterns}", refresh=args.refresh)
        _print_answer(answer)
        return
        
    if args.news:
        answer = ask_question(f"/news {args.news}", refresh=args.refresh)
        _print_answer(answer)
        return
        
    if args.optimize:
        answer = ask_question("/optimize", refresh=args.refresh)
        _print_answer(answer)
        return
        
    if args.scenarios:
        answer = ask_question("/scenarios", refresh=args.refresh)
        _print_answer(answer)
        return
        
    # If no question provided, enter interactive mode
    if not args.question:
        if RICH_AVAILABLE:
            console.print(Panel.fit("OpenMT4TradingBot Chat Interface", style="blue"))
            console.print(Panel("""Comandi speciali:
/analyze [symbol] - Analizza i fattori di mercato
/patterns [symbol] - Identifica pattern tecnici
/news [symbol] - Mostra le ultime notizie
/optimize - Ottimizza il portafoglio
/scenarios - Analisi scenari di mercato
/help - Mostra questo messaggio

'exit' o 'quit' per uscire, 'refresh' per aggiornare il contesto""", title="Aiuto", border_style="green"))
            
            while True:
                question = console.input("[bold blue]> [/bold blue]")
                
                if question.lower() in ["exit", "quit"]:
                    break
                    
                if question.lower() == "refresh":
                    context_manager.refresh()
                    console.print("[green]Contesto aggiornato[/green]")
                    continue
                
                if question.lower() in ["help", "aiuto", "?"]:
                    question = "/help"
                    
                answer = ask_question(question)
                console.print(Markdown(answer))
                print()
        else:
            print("OpenMT4TradingBot Chat Interface")
            print("Comandi speciali: /analyze, /patterns, /news, /optimize, /scenarios, /help")
            print("Type 'exit' or 'quit' to exit, 'refresh' to refresh context")
            
            while True:
                question = input("> ")
                
                if question.lower() in ["exit", "quit"]:
                    break
                    
                if question.lower() == "refresh":
                    context_manager.refresh()
                    print("Contesto aggiornato")
                    continue
                    
                if question.lower() in ["help", "aiuto", "?"]:
                    question = "/help"
                    
                answer = ask_question(question)
                print(answer)
                print()
                
    # Answer single question
    else:
        answer = ask_question(args.question, refresh=args.refresh)
        _print_answer(answer)


def _print_answer(answer):
    """Helper function to print an answer with formatting if available."""
    if RICH_AVAILABLE:
        console.print(Markdown(answer))
    else:
        print(answer)


if __name__ == "__main__":
    run_cli()
