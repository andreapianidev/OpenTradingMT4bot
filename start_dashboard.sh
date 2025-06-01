#!/bin/bash

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funzione per il logo ASCII
print_logo() {
    echo -e "${BLUE}"
    echo "  ___                  __  __ _____ _  _   _____               _ _             ____        _   "
    echo " / _ \ _ __   ___ _ __|  \/  |_   _| || | |_   _| __ __ _  __| (_)_ __   __ _| __ )  ___ | |_ "
    echo "| | | | '_ \ / _ \ '_ \ |\/| | | | | || |_  | || '__/ _\` |/ _\` | | '_ \ / _\` |  _ \ / _ \| __|"
    echo "| |_| | |_) |  __/ | | | |  | | | | |__   _| | || | | (_| | (_| | | | | | (_| | |_) | (_) | |_ "
    echo " \___/| .__/ \___|_| |_|_|  |_| |_|    |_|   |_||_|  \__,_|\__,_|_|_| |_|\__, |____/ \___/ \__|"
    echo "      |_|                                                                |___/                  "
    echo -e "${NC}"
    echo -e "${CYAN}Dashboard Launcher${NC}"
    echo -e "${YELLOW}=====================================${NC}"
}

# Funzione per verificare se una porta è in uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0 # porta in uso
    else
        return 1 # porta libera
    fi
}

# Funzione per avviare il server API
start_api_server() {
    echo -e "${YELLOW}Avvio del server API...${NC}"
    if check_port 8000; then
        echo -e "${RED}La porta 8000 è già in uso. Impossibile avviare il server API.${NC}"
        return 1
    fi
    
    # Attiva l'ambiente virtuale se esiste
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Crea la cartella logs se non esiste
    mkdir -p logs
    
    # Avvia il server API in background
    python python/api_server.py > logs/api_server.log 2>&1 &
    API_PID=$!
    echo -e "${GREEN}Server API avviato (PID: $API_PID)${NC}"
    echo -e "${BLUE}Per visualizzare i log: tail -f logs/api_server.log${NC}"
    
    # Verifica che il server sia partito correttamente
    sleep 3
    if ps -p $API_PID > /dev/null; then
        echo -e "${GREEN}Server API avviato correttamente!${NC}"
        echo $API_PID > .api_server.pid
    else
        echo -e "${RED}Errore nell'avvio del server API. Controlla i log per dettagli.${NC}"
        return 1
    fi
}

# Funzione per avviare l'interfaccia React
start_react_interface() {
    echo -e "${YELLOW}Avvio dell'interfaccia React...${NC}"
    if check_port 3000; then
        echo -e "${RED}La porta 3000 è già in uso. Impossibile avviare l'interfaccia React.${NC}"
        return 1
    fi
    
    cd web-dashboard
    
    # Installa le dipendenze se necessario
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installazione delle dipendenze...${NC}"
        npm install
    fi
    
    # Avvia l'interfaccia React in background
    npm run dev > ../logs/react_interface.log 2>&1 &
    REACT_PID=$!
    echo -e "${GREEN}Interfaccia React avviata (PID: $REACT_PID)${NC}"
    echo -e "${BLUE}Per visualizzare i log: tail -f logs/react_interface.log${NC}"
    
    cd ..
    
    # Verifica che l'interfaccia sia partita correttamente
    sleep 5
    if ps -p $REACT_PID > /dev/null; then
        echo -e "${GREEN}Interfaccia React avviata correttamente!${NC}"
        echo $REACT_PID > .react_interface.pid
    else
        echo -e "${RED}Errore nell'avvio dell'interfaccia React. Controlla i log per dettagli.${NC}"
        return 1
    fi
}

# Funzione per costruire l'interfaccia React per la produzione
build_react_interface() {
    echo -e "${YELLOW}Costruzione dell'interfaccia React per la produzione...${NC}"
    
    cd web-dashboard
    
    # Installa le dipendenze se necessario
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installazione delle dipendenze...${NC}"
        npm install
    fi
    
    # Costruisci l'interfaccia React
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Interfaccia React costruita correttamente!${NC}"
        echo -e "${BLUE}I file di build sono disponibili in: web-dashboard/build${NC}"
    else
        echo -e "${RED}Errore nella costruzione dell'interfaccia React.${NC}"
        return 1
    fi
    
    cd ..
}

# Funzione per fermare il server API e l'interfaccia React
stop_services() {
    echo -e "${YELLOW}Arresto dei servizi...${NC}"
    
    # Ferma il server API
    if [ -f .api_server.pid ]; then
        API_PID=$(cat .api_server.pid)
        if ps -p $API_PID > /dev/null; then
            echo -e "${YELLOW}Arresto del server API (PID: $API_PID)...${NC}"
            kill $API_PID
            rm .api_server.pid
        else
            echo -e "${RED}Il server API non è in esecuzione.${NC}"
        fi
    else
        echo -e "${RED}File PID del server API non trovato.${NC}"
    fi
    
    # Ferma l'interfaccia React
    if [ -f .react_interface.pid ]; then
        REACT_PID=$(cat .react_interface.pid)
        if ps -p $REACT_PID > /dev/null; then
            echo -e "${YELLOW}Arresto dell'interfaccia React (PID: $REACT_PID)...${NC}"
            kill $REACT_PID
            rm .react_interface.pid
        else
            echo -e "${RED}L'interfaccia React non è in esecuzione.${NC}"
        fi
    else
        echo -e "${RED}File PID dell'interfaccia React non trovato.${NC}"
    fi
    
    echo -e "${GREEN}Tutti i servizi sono stati arrestati.${NC}"
}

# Funzione per aprire il browser
open_dashboard() {
    echo -e "${YELLOW}Apertura della dashboard nel browser...${NC}"
    
    # Apri il browser (compatibile con macOS, Linux e Windows)
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        open http://localhost:3000
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        # Linux
        xdg-open http://localhost:3000
    elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
        # Windows
        start http://localhost:3000
    else
        echo -e "${RED}Sistema operativo non supportato per l'apertura automatica del browser.${NC}"
        echo -e "${YELLOW}Apri manualmente il browser e vai a: http://localhost:3000${NC}"
    fi
}

# Funzione principale del menu
main_menu() {
    clear
    print_logo
    
    echo -e "${CYAN}Menu principale:${NC}"
    echo -e "${YELLOW}1.${NC} Avvia server API e interfaccia React"
    echo -e "${YELLOW}2.${NC} Avvia solo server API"
    echo -e "${YELLOW}3.${NC} Avvia solo interfaccia React"
    echo -e "${YELLOW}4.${NC} Costruisci interfaccia React per produzione"
    echo -e "${YELLOW}5.${NC} Apri dashboard nel browser"
    echo -e "${YELLOW}6.${NC} Ferma tutti i servizi"
    echo -e "${YELLOW}7.${NC} Esci"
    echo -e "${YELLOW}=====================================${NC}"
    
    read -p "Seleziona un'opzione [1-7]: " choice
    
    case $choice in
        1)
            start_api_server
            start_react_interface
            echo -e "${GREEN}Dashboard disponibile all'indirizzo: http://localhost:3000${NC}"
            echo -e "${BLUE}API disponibile all'indirizzo: http://localhost:8000${NC}"
            ;;
        2)
            start_api_server
            ;;
        3)
            start_react_interface
            echo -e "${GREEN}Dashboard disponibile all'indirizzo: http://localhost:3000${NC}"
            ;;
        4)
            build_react_interface
            ;;
        5)
            open_dashboard
            ;;
        6)
            stop_services
            ;;
        7)
            echo -e "${GREEN}Arrivederci!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opzione non valida.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Premi Enter per continuare..."
    main_menu
}

# Avvia il menu principale
main_menu
