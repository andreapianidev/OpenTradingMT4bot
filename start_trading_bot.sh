#!/bin/bash

# ==========================================
# OpenMT4TradingBot - Launch Control Script
# ==========================================
# Copyright (c) 2025 Immaginet Srl
# 
# Questo script avvia e gestisce tutti i componenti Python
# necessari per il funzionamento completo di OpenMT4TradingBot.

# Colori per output più leggibile
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
PURPLE="\033[0;35m"
CYAN="\033[0;36m"
RESET="\033[0m"
BOLD="\033[1m"

# Variabili globali
PYTHON_CMD="python3"
VENV_DIR="venv"
LOG_DIR="logs"
SIGNAL_PID_FILE="/tmp/openmttrading_signal.pid"
CHAT_PID_FILE="/tmp/openmttrading_chat.pid"
WEB_PID_FILE="/tmp/openmttrading_web.pid"

# Funzione per stampare il logo ASCII
print_logo() {
    clear
    echo -e "${BLUE}${BOLD}"
    echo "  ____                   __  __ _____ _  _   _____               _ _             ____        _   "
    echo " / __ \                 |  \/  |_   _| || | |_   _|             | (_)           |  _ \      | |  "
    echo "| |  | |_ __   ___ _ __ | \  / | | | | || |_  | |_ __ __ _  __ _| |_ _ __   __ _| |_) | ___ | |_ "
    echo "| |  | | '_ \ / _ \ '_ \| |\/| | | | |__   _| | | '__/ _\` |/ _\` | | | '_ \ / _\` |  _ < / _ \| __|"
    echo "| |__| | |_) |  __/ | | | |  | |_| |_  | |   | | | | (_| | (_| | | | | | | (_| | |_) | (_) | |_ "
    echo " \____/| .__/ \___|_| |_|_|  |_|_____| |_|   |_|_|  \__,_|\__,_|_|_|_| |_|\__, |____/ \___/ \__|"
    echo "       | |                                                                 __/ |                 "
    echo "       |_|                                                                |___/                  "
    echo -e "${RESET}"
    echo -e "${CYAN}============================== Pannello di Controllo ==============================${RESET}"
    echo
}

# Funzione per verificare e creare la directory dei log
setup_logs() {
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        echo -e "${GREEN}Directory dei log creata: $LOG_DIR${RESET}"
    fi
}

# Funzione per verificare che Python sia installato
check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}Python 3 non è installato. Per favore installalo prima di continuare.${RESET}"
        exit 1
    fi
    
    echo -e "${GREEN}Python $(python3 --version | cut -d' ' -f2) trovato.${RESET}"
}

# Funzione per verificare e attivare l'ambiente virtuale
check_venv() {
    # Se siamo già in un ambiente virtuale, skippiamo
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo -e "${GREEN}Ambiente virtuale già attivo: $VIRTUAL_ENV${RESET}"
        return 0
    fi
    
    # Verifichiamo se esiste l'ambiente virtuale
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}Attivazione dell'ambiente virtuale...${RESET}"
        
        # Attiva l'ambiente virtuale
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            source $VENV_DIR/Scripts/activate
        else
            source $VENV_DIR/bin/activate
        fi
        
        echo -e "${GREEN}Ambiente virtuale attivato.${RESET}"
    else
        echo -e "${YELLOW}Ambiente virtuale non trovato. Vuoi crearne uno nuovo? [s/n]${RESET}"
        read -p "" create_venv
        
        if [[ $create_venv == "s" || $create_venv == "S" ]]; then
            echo -e "${GREEN}Creazione dell'ambiente virtuale...${RESET}"
            $PYTHON_CMD -m venv $VENV_DIR
            
            # Attiva l'ambiente virtuale
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                source $VENV_DIR/Scripts/activate
            else
                source $VENV_DIR/bin/activate
            fi
            
            echo -e "${GREEN}Ambiente virtuale creato e attivato.${RESET}"
            
            # Installa le dipendenze
            echo -e "${GREEN}Installazione delle dipendenze...${RESET}"
            pip install -r python/requirements.txt
        else
            echo -e "${YELLOW}Continuando senza ambiente virtuale. Assicurati che tutte le dipendenze siano installate.${RESET}"
        fi
    fi
}

# Funzione per verificare se .env esiste e contiene la chiave API DeepSeek
check_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}File .env non trovato. Creazione del file .env di esempio...${RESET}"
        echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
        echo "DEEPSEEK_MODEL=deepseek-chat" >> .env
        echo "DEEPSEEK_API_BASE=https://api.deepseek.com/v1" >> .env
        echo -e "${RED}Per favore modifica il file .env con la tua chiave API DeepSeek prima di continuare.${RESET}"
        echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
        read
    else
        # Verifica se contiene una chiave API valida
        DEEPSEEK_KEY=$(grep DEEPSEEK_API_KEY .env | cut -d= -f2)
        if [ "$DEEPSEEK_KEY" = "your_api_key_here" ] || [ -z "$DEEPSEEK_KEY" ]; then
            echo -e "${RED}ATTENZIONE: Chiave API DeepSeek non configurata nel file .env${RESET}"
            echo -e "${RED}Alcune funzionalità potrebbero non essere disponibili.${RESET}"
            echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
            read
        else
            echo -e "${GREEN}Configurazione DeepSeek trovata.${RESET}"
        fi
    fi
}

# Funzione per avviare il motore dei segnali
start_signal_engine() {
    echo -e "${GREEN}Avvio del motore dei segnali in background...${RESET}"
    nohup $PYTHON_CMD python/signal_engine.py > $LOG_DIR/signal_engine.log 2>&1 &
    echo $! > $SIGNAL_PID_FILE
    echo -e "${GREEN}Motore dei segnali avviato. PID: $(cat $SIGNAL_PID_FILE)${RESET}"
    echo -e "${GREEN}Log disponibile in: $LOG_DIR/signal_engine.log${RESET}"
}

# Funzione per avviare l'interfaccia chat
start_chat_interface() {
    echo -e "${GREEN}Avvio dell'interfaccia chat in background...${RESET}"
    nohup $PYTHON_CMD python/chat_interface.py > $LOG_DIR/chat_interface.log 2>&1 &
    echo $! > $CHAT_PID_FILE
    echo -e "${GREEN}Interfaccia chat avviata. PID: $(cat $CHAT_PID_FILE)${RESET}"
    echo -e "${GREEN}Log disponibile in: $LOG_DIR/chat_interface.log${RESET}"
}

# Funzione per avviare l'interfaccia web
start_web_interface() {
    echo -e "${GREEN}Avvio dell'interfaccia web in background...${RESET}"
    nohup $PYTHON_CMD python/chat_interface.py --server --port 8000 > $LOG_DIR/web_interface.log 2>&1 &
    echo $! > $WEB_PID_FILE
    echo -e "${GREEN}Interfaccia web avviata. PID: $(cat $WEB_PID_FILE)${RESET}"
    echo -e "${GREEN}Accedi all'interfaccia web all'indirizzo: http://localhost:8000${RESET}"
    echo -e "${GREEN}Log disponibile in: $LOG_DIR/web_interface.log${RESET}"
}

# Funzione per mostrare un grafico interattivo
show_chart() {
    echo -e "${CYAN}Generazione grafico interattivo${RESET}"
    echo -e "${YELLOW}Scegli un simbolo:${RESET}"
    echo "1) XAUUSD (Oro)"
    echo "2) XAGUSD (Argento)"
    echo "3) WTICOUSD (Petrolio WTI)"
    echo "4) BCOUSD (Petrolio Brent)"
    echo "5) NATGASUSD (Gas Naturale)"
    echo "6) CORNUSD (Mais)"
    echo "7) SOYBNUSD (Soia)"
    echo "8) WHEATUSD (Grano)"
    echo "9) Inserisci un simbolo personalizzato"
    echo "0) Torna al menu principale"
    read -p "Scelta: " chart_choice
    
    case $chart_choice in
        1) symbol="XAUUSD" ;;
        2) symbol="XAGUSD" ;;
        3) symbol="WTICOUSD" ;;
        4) symbol="BCOUSD" ;;
        5) symbol="NATGASUSD" ;;
        6) symbol="CORNUSD" ;;
        7) symbol="SOYBNUSD" ;;
        8) symbol="WHEATUSD" ;;
        9) 
            read -p "Inserisci il simbolo: " symbol
            symbol=$(echo $symbol | tr '[:lower:]' '[:upper:]')
            ;;
        0) return ;;
        *) 
            echo -e "${RED}Scelta non valida.${RESET}"
            return
            ;;
    esac
    
    echo -e "${YELLOW}Scegli un periodo:${RESET}"
    echo "1) 1 mese (1mo)"
    echo "2) 3 mesi (3mo)"
    echo "3) 6 mesi (6mo)"
    echo "4) 1 anno (1y)"
    echo "5) 2 anni (2y)"
    echo "6) 5 anni (5y)"
    echo "7) Max (max)"
    echo "8) Inserisci un periodo personalizzato"
    read -p "Scelta: " period_choice
    
    case $period_choice in
        1) period="1mo" ;;
        2) period="3mo" ;;
        3) period="6mo" ;;
        4) period="1y" ;;
        5) period="2y" ;;
        6) period="5y" ;;
        7) period="max" ;;
        8) 
            read -p "Inserisci il periodo (es. 1d, 5d, 1mo, 3mo, 1y, 2y, 5y, max): " period
            ;;
        *) 
            echo -e "${RED}Scelta non valida. Uso il periodo predefinito di 1 anno.${RESET}"
            period="1y"
            ;;
    esac
    
    echo -e "${YELLOW}Scegli un intervallo:${RESET}"
    echo "1) Giornaliero (1d)"
    echo "2) Settimanale (1wk)"
    echo "3) Mensile (1mo)"
    echo "4) Orario (1h)"
    echo "5) Inserisci un intervallo personalizzato"
    read -p "Scelta: " interval_choice
    
    case $interval_choice in
        1) interval="1d" ;;
        2) interval="1wk" ;;
        3) interval="1mo" ;;
        4) interval="1h" ;;
        5) 
            read -p "Inserisci l'intervallo (es. 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo): " interval
            ;;
        *) 
            echo -e "${RED}Scelta non valida. Uso l'intervallo predefinito di 1 giorno.${RESET}"
            interval="1d"
            ;;
    esac
    
    echo -e "${GREEN}Generazione del grafico per $symbol (periodo: $period, intervallo: $interval)...${RESET}"
    $PYTHON_CMD -c "import sys; sys.path.append('python'); from charting_utils import get_commodity_data, plot_candlestick_chart; import webbrowser; import tempfile; from pathlib import Path; data = get_commodity_data('$symbol', period='$period', interval='$interval'); fig = plot_candlestick_chart(data, symbol_display='$symbol') if data is not None and not data.empty else None; tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') if fig is not None else None; fig.write_html(tmp_file.name) if fig is not None else None; webbrowser.open_new_tab(Path(tmp_file.name).resolve().as_uri()) if fig is not None else print('Errore: Impossibile generare il grafico. Verifica il simbolo e i parametri.')"
    
    echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
    read
}

# Funzione per arrestare un processo tramite il suo file PID
stop_process() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -e "${YELLOW}Arresto di $name (PID: $pid)...${RESET}"
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}$name arrestato.${RESET}"
        else
            echo -e "${YELLOW}$name non è in esecuzione.${RESET}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}$name non è in esecuzione.${RESET}"
    fi
}

# Funzione per controllare lo stato di un processo
check_process_status() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo -e "${GREEN}$name è in esecuzione. PID: $pid${RESET}"
            return 0
        else
            echo -e "${RED}$name risulta in esecuzione ma il processo è morto.${RESET}"
            rm "$pid_file"
            return 1
        fi
    else
        echo -e "${YELLOW}$name non è in esecuzione.${RESET}"
        return 1
    fi
}

# Funzione per controllare lo stato di tutti i processi
check_all_status() {
    echo -e "${CYAN}Stato dei servizi:${RESET}"
    check_process_status "$SIGNAL_PID_FILE" "Motore dei segnali"
    check_process_status "$CHAT_PID_FILE" "Interfaccia chat"
    check_process_status "$WEB_PID_FILE" "Interfaccia web"
    
    echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
    read
}

# Funzione per mostrare la visualizzazione dei log
view_logs() {
    echo -e "${CYAN}Visualizzazione dei log:${RESET}"
    echo "1) Log del motore dei segnali"
    echo "2) Log dell'interfaccia chat"
    echo "3) Log dell'interfaccia web"
    echo "0) Torna al menu principale"
    read -p "Scelta: " log_choice
    
    case $log_choice in
        1) 
            if [ -f "$LOG_DIR/signal_engine.log" ]; then
                echo -e "${GREEN}Ultime 20 righe del log del motore dei segnali:${RESET}"
                tail -n 20 "$LOG_DIR/signal_engine.log"
            else
                echo -e "${RED}File di log non trovato.${RESET}"
            fi
            ;;
        2) 
            if [ -f "$LOG_DIR/chat_interface.log" ]; then
                echo -e "${GREEN}Ultime 20 righe del log dell'interfaccia chat:${RESET}"
                tail -n 20 "$LOG_DIR/chat_interface.log"
            else
                echo -e "${RED}File di log non trovato.${RESET}"
            fi
            ;;
        3) 
            if [ -f "$LOG_DIR/web_interface.log" ]; then
                echo -e "${GREEN}Ultime 20 righe del log dell'interfaccia web:${RESET}"
                tail -n 20 "$LOG_DIR/web_interface.log"
            else
                echo -e "${RED}File di log non trovato.${RESET}"
            fi
            ;;
        0) return ;;
        *) echo -e "${RED}Scelta non valida.${RESET}" ;;
    esac
    
    echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
    read
}

# Funzione per avviare tutti i servizi
start_all_services() {
    echo -e "${CYAN}Avvio di tutti i servizi...${RESET}"
    start_signal_engine
    start_chat_interface
    start_web_interface
    
    echo -e "${GREEN}Tutti i servizi sono stati avviati.${RESET}"
    echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
    read
}

# Funzione per arrestare tutti i servizi
stop_all_services() {
    echo -e "${CYAN}Arresto di tutti i servizi...${RESET}"
    stop_process "$SIGNAL_PID_FILE" "Motore dei segnali"
    stop_process "$CHAT_PID_FILE" "Interfaccia chat"
    stop_process "$WEB_PID_FILE" "Interfaccia web"
    
    echo -e "${GREEN}Tutti i servizi sono stati arrestati.${RESET}"
    echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"
    read
}

# Menu principale
main_menu() {
    while true; do
        print_logo
        
        # Mostra lo stato corrente dei servizi
        echo -e "${CYAN}Stato attuale:${RESET}"
        check_process_status "$SIGNAL_PID_FILE" "Motore dei segnali" > /dev/null && echo -e "${GREEN}• Motore dei segnali: Attivo${RESET}" || echo -e "${RED}• Motore dei segnali: Inattivo${RESET}"
        check_process_status "$CHAT_PID_FILE" "Interfaccia chat" > /dev/null && echo -e "${GREEN}• Interfaccia chat: Attiva${RESET}" || echo -e "${RED}• Interfaccia chat: Inattiva${RESET}"
        check_process_status "$WEB_PID_FILE" "Interfaccia web" > /dev/null && echo -e "${GREEN}• Interfaccia web: Attiva${RESET}" || echo -e "${RED}• Interfaccia web: Inattiva${RESET}"
        
        echo
        echo -e "${CYAN}Avvio servizi:${RESET}"
        echo "1) Avvia tutti i servizi"
        echo "2) Avvia il motore dei segnali"
        echo "3) Avvia l'interfaccia chat"
        echo "4) Avvia l'interfaccia web"
        
        echo
        echo -e "${CYAN}Gestione servizi:${RESET}"
        echo "5) Arresta tutti i servizi"
        echo "6) Controlla lo stato dei servizi"
        echo "7) Visualizza i log"
        
        echo
        echo -e "${CYAN}Funzionalità:${RESET}"
        echo "8) Genera un grafico interattivo"
        
        echo
        echo -e "${CYAN}Sistema:${RESET}"
        echo "0) Esci"
        
        echo
        read -p "Scelta: " choice
        
        case $choice in
            1) start_all_services ;;
            2) start_signal_engine; echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"; read ;;
            3) start_chat_interface; echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"; read ;;
            4) start_web_interface; echo -e "${YELLOW}Premi INVIO per continuare...${RESET}"; read ;;
            5) stop_all_services ;;
            6) check_all_status ;;
            7) view_logs ;;
            8) show_chart ;;
            0) 
                echo -e "${GREEN}Arrivederci!${RESET}"
                exit 0
                ;;
            *) 
                echo -e "${RED}Scelta non valida.${RESET}"
                sleep 2
                ;;
        esac
    done
}

# ===== Esecuzione principale =====

# Verifica che lo script sia eseguito da bash
if [ -z "$BASH_VERSION" ]; then
    echo "Questo script richiede bash. Per favore eseguilo con: bash $0"
    exit 1
fi

# Configurazione iniziale
setup_logs
check_python
check_venv
check_env

# Avvia il menu principale
main_menu
