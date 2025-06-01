#!/bin/bash

# ==========================================
# OpenMT4TradingBot - Installation Script
# ==========================================
# Copyright (c) 2025 Immaginet Srl
# 
# Script di installazione per i componenti Python di OpenMT4TradingBot

# Colori per output più leggibile
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"
BOLD="\033[1m"

# Stampa il logo ASCII
echo -e "${BLUE}${BOLD}"
echo "  ____                   __  __ _____ _  _   _____               _ _             ____        _   "
echo " / __ \\                 |  \\/  |_   _| || | |_   _|             | (_)           |  _ \\      | |  "
echo "| |  | |_ __   ___ _ __ | \\  / | | | | || |_  | |_ __ __ _  __ _| |_ _ __   __ _| |_) | ___ | |_ "
echo "| |  | | '_ \\ / _ \\ '_ \\| |\\/| | | | |__   _| | | '__/ _\` |/ _\` | | | '_ \\ / _\` |  _ < / _ \\| __|"
echo "| |__| | |_) |  __/ | | | |  | |_| |_  | |   | | | | (_| | (_| | | | | | | (_| | |_) | (_) | |_ "
echo " \\____/| .__/ \\___|_| |_|_|  |_|_____| |_|   |_|_|  \\__,_|\\__,_|_|_|_| |_|\\__, |____/ \\___/ \\__|"
echo "       | |                                                                 __/ |                 "
echo "       |_|                                                                |___/                  "
echo -e "${RESET}"
echo -e "${GREEN}============================== Installazione ==============================${RESET}"
echo

# Verifica che Python sia installato
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 non è installato. Per favore installalo prima di continuare.${RESET}"
    exit 1
fi

echo -e "${GREEN}Python $(python3 --version | cut -d' ' -f2) trovato.${RESET}"

# Crea un ambiente virtuale (opzionale)
echo -e "${YELLOW}Vuoi creare un ambiente virtuale Python? (consigliato) [s/n]: ${RESET}"
read -p "" create_venv
if [[ $create_venv == "s" || $create_venv == "S" ]]; then
    echo -e "${GREEN}Creazione dell'ambiente virtuale...${RESET}"
    python3 -m venv venv
    
    # Attiva l'ambiente virtuale
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    echo -e "${GREEN}Ambiente virtuale creato e attivato.${RESET}"
else
    echo -e "${YELLOW}Continuando senza ambiente virtuale. Assicurati che tutte le dipendenze siano installate globalmente.${RESET}"
fi

# Installa le dipendenze
echo -e "${GREEN}Installazione delle dipendenze...${RESET}"
pip3 install -r python/requirements.txt

# Crea la directory dei log se non esiste
if [ ! -d "logs" ]; then
    echo -e "${GREEN}Creazione della directory dei log...${RESET}"
    mkdir -p logs
fi

# Verifica se è presente un file .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creazione del file .env di esempio...${RESET}"
    echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
    echo "DEEPSEEK_MODEL=deepseek-chat" >> .env
    echo "DEEPSEEK_API_BASE=https://api.deepseek.com/v1" >> .env
    echo -e "${YELLOW}File .env creato. Per favore modifica il file con la tua chiave API DeepSeek.${RESET}"
else
    echo -e "${GREEN}File .env già esistente.${RESET}"
    
    # Verifica se contiene una chiave API valida
    DEEPSEEK_KEY=$(grep DEEPSEEK_API_KEY .env | cut -d= -f2)
    if [ "$DEEPSEEK_KEY" = "your_api_key_here" ] || [ -z "$DEEPSEEK_KEY" ]; then
        echo -e "${RED}ATTENZIONE: Chiave API DeepSeek non configurata nel file .env${RESET}"
        echo -e "${RED}Alcune funzionalità potrebbero non essere disponibili.${RESET}"
    else
        echo -e "${GREEN}Configurazione DeepSeek trovata.${RESET}"
    fi
fi

# Rendi eseguibile lo script di avvio
chmod +x start_trading_bot.sh

# Messaggio finale
echo -e "\n${GREEN}${BOLD}Installazione completata con successo!${RESET}\n"
echo -e "${YELLOW}Per avviare il bot con l'interfaccia grafica:${RESET}"
echo -e "   ${GREEN}./start_trading_bot.sh${RESET}"
echo
echo -e "${YELLOW}Per avviare manualmente i componenti:${RESET}"
echo -e "   ${GREEN}python3 python/signal_engine.py${RESET}     (Motore dei segnali)"
echo -e "   ${GREEN}python3 python/chat_interface.py${RESET}   (Interfaccia chat)"
echo -e "   ${GREEN}python3 python/chat_interface.py --server --port 8000${RESET} (Server web)"
echo
echo -e "${BLUE}${BOLD}Vuoi avviare ora l'interfaccia di controllo? [s/n]${RESET}"
read -p "" start_now
if [[ $start_now == "s" || $start_now == "S" ]]; then
    ./start_trading_bot.sh
else
    echo -e "${GREEN}Puoi avviare l'interfaccia in qualsiasi momento con ./start_trading_bot.sh${RESET}"
fi
