#!/bin/bash

# Script di installazione per i componenti Python di OpenMT4TradingBot
echo "Installazione dei componenti Python di OpenMT4TradingBot..."

# Verifica che Python sia installato
if ! command -v python3 &> /dev/null; then
    echo "Python 3 non è installato. Per favore installalo prima di continuare."
    exit 1
fi

# Crea un ambiente virtuale (opzionale)
read -p "Vuoi creare un ambiente virtuale Python? (consigliato) [s/n]: " create_venv
if [[ $create_venv == "s" || $create_venv == "S" ]]; then
    echo "Creazione dell'ambiente virtuale..."
    python3 -m venv venv
    
    # Attiva l'ambiente virtuale
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    echo "Ambiente virtuale creato e attivato."
fi

# Installa le dipendenze
echo "Installazione delle dipendenze..."
pip3 install -r python/requirements.txt

# Verifica se è presente un file .env
if [ ! -f .env ]; then
    echo "Creazione del file .env di esempio..."
    echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
    echo "DEEPSEEK_MODEL=deepseek-chat" >> .env
    echo "DEEPSEEK_API_BASE=https://api.deepseek.com/v1" >> .env
    echo "File .env creato. Per favore modifica il file con la tua chiave API DeepSeek."
else
    echo "File .env già esistente."
fi

echo "Installazione completata!"
echo "Per avviare il motore di segnali: python3 python/signal_engine.py"
echo "Per avviare l'interfaccia chat: python3 python/chat_interface.py"
echo "Per avviare l'interfaccia web: python3 python/chat_interface.py --server --port 8000"
