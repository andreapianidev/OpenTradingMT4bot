# OpenMT4TradingBot

Un bot di trading ibrido MT4 + Python per i mercati delle commodity con integrazione dell'AI DeepSeek. Interfaccia Web React Native

## Panoramica

OpenMT4TradingBot è un sistema di trading open-source che combina MetaTrader 4 (MT4) con Python per creare una potente soluzione di trading per i mercati delle commodity. Il bot utilizza una strategia di breakout Donchian con filtri COT (Commitment of Traders) e stagionali per generare segnali di trading su diversi mercati delle commodity.

Il sistema è diviso in due componenti principali:
1. **Expert Advisor MT4**: Gestisce l'esecuzione degli ordini, la gestione dello stop-loss/take-profit e l'esportazione dei dati
2. **Motore di Segnali Python**: Calcola i segnali di trading, applica i filtri e comunica con l'EA tramite un ponte basato su file

## Strategia di Trading

OpenMT4TradingBot implementa un sofisticato approccio di trading multi-fattore progettato specificamente per i mercati delle commodity:

1. **Strategia Core - Breakout Donchian**: Il sistema utilizza canali Donchian da 40 barre sul timeframe D1 per identificare significativi breakout di prezzo. Questo approccio sfrutta la tendenza delle commodity a sviluppare trend sostenuti dopo i breakout di range.

2. **Filtri Intelligenti**:
   - **Filtro COT**: Analizza i dati del Commitment of Traders della CFTC per valutare il posizionamento di mercato dei diversi tipi di trader (hedger commerciali, grandi speculatori, piccoli trader). Questo fornisce informazioni cruciali sul sentiment istituzionale e aiuta a evitare di operare contro le forze dominanti del mercato.
   - **Filtro Stagionale**: Le commodity spesso mostrano pattern stagionali dovuti a cicli di produzione, condizioni meteorologiche e pattern di consumo. Il bot sfrutta le tendenze stagionali storiche per ottimizzare il timing di entrata e il dimensionamento delle posizioni.

3. **Gestione Avanzata del Rischio**:
   - **Stop-Loss Adattivo**: Utilizza l'Average True Range (ATR) per impostare livelli di stop-loss che si adattano alla volatilità corrente del mercato
   - **Take-Profit Intelligente**: Imposta obiettivi di profitto basati sulla volatilità storica e sui livelli di supporto/resistenza
   - **Trailing Stop Dinamico**: Protegge i profitti permettendo allo stesso tempo ai trend di svilupparsi completamente
   - **Dimensionamento delle Posizioni basato sulla Volatilità**: Regola la dimensione della posizione in base all'ATR per mantenere un rischio costante su diverse commodity

4. **Potenziamento con DeepSeek AI**:
   - **Analisi del Sentimento di Mercato**: Valuta notizie e narrative di mercato per identificare cambiamenti nel sentimento
   - **Analisi di Mercato Multi-Fattoriale**: Combina dati tecnici, fondamentali e di sentimento
   - **Riconoscimento di Pattern Tecnici**: Identifica pattern grafici complessi che complementano i segnali di breakout
   - **Ottimizzazione del Portafoglio**: Suggerisce un'allocazione ottimale tra diverse commodity
   - **Analisi di Scenario**: Stress-test delle strategie in diverse condizioni di mercato

## Why This Bot Is Valuable

- **Architettura ibrida**: Combina l'esecuzione affidabile di MT4 con le capacità analitiche avanzate di Python
- **Focalizzazione sulle commodity**: Progettato specificamente per le caratteristiche uniche dei mercati delle commodity
- **Approccio multi-fattore**: Integra azione di prezzo, struttura del mercato, sentimento e stagionalità
- **Gestione del rischio intelligente**: Si adatta alle condizioni di mercato in evoluzione con controlli di rischio sofisticati
- **Decisioni potenziate dall'AI**: Sfrutta DeepSeek AI per insights di mercato più profondi oltre gli indicatori tradizionali
- **Interfaccia conversazionale**: Interazione in linguaggio naturale per i trader per interrogare il sistema su mercati e strategia
- **Design estendibile**: Facile da personalizzare ed espandere con strategie o commodity aggiuntive
- **Open Source**: Implementazione trasparente che può essere verificata e modificata

## Funzionalità

- **Strategia di Breakout Donchian**: Utilizza canali Donchian da 40 barre sul timeframe D1
- **Filtro COT**: Analizza i dati del Commitment of Traders per ingressi di trading intelligenti
- **Filtro Stagionale**: Applica pattern di stagionalità per ottimizzare il dimensionamento delle posizioni
- **Gestione del Rischio**: Stop-loss, take-profit e trailing stop basati su ATR
- **Parità di Volatilità**: Dimensionamento delle posizioni basato sulla volatilità ATR
- **Integrazione DeepSeek AI**: Analisi del sentimento e interfaccia Q&A in linguaggio naturale
- **Bridge basato su file**: Comunicazione semplice e affidabile tra MT4 e Python

## Simboli Supportati

### Metalli Preziosi
- Oro (XAUUSD)
- Argento (XAGUSD)
- Platino (XPTUSD)
- Palladio (XPDUSD)

### Energia
- Petrolio Greggio WTI (WTICOUSD)
- Petrolio Greggio Brent (BCOUSD)
- Gas Naturale (NATGASUSD)
- Olio da Riscaldamento (HOIL)
- Benzina RBOB (RBOB)

### Agricoli
- Mais (CORNUSD)
- Soia (SOYBNUSD)
- Grano (WHEATUSD)
- Caffè (COFFEE)
- Cotone (COTTON)
- Zucchero (SUGAR)
- Cacao (COCOA)
- Succo d'Arancia (OJ)

### Metalli Base
- Rame (XCUUSD)
- Alluminio (XALUSD)
- Nichel (XNIUSD)
- Zinco (XZNUSD)
- Piombo (XPBUSD)

## Requisiti

### MetaTrader 4
- Piattaforma MT4 (build 1320 o superiore)
- Compilatore MQL4

### Python
- Python 3.8 o superiore
- Pacchetti richiesti:
  - pandas
  - numpy
  - requests
  - schedule
  - pyarrow
  - fastapi (optional, for web interface)
  - uvicorn (optional, for web interface)
  - rich (optional, for CLI interface)

## Installation

### MetaTrader 4 Setup
1. Copy `mql4/OpenMT4TradingBot.mq4` to your MT4 `MQL4/Experts` directory
2. Compile the EA in the MetaEditor
3. Create a directory `Files/OpenMT4TradingBot` in your MT4 data folder

### Python Setup

#### Metodo automatico (consigliato)
1. Esegui lo script di installazione automatico:
   ```bash
   # Su Linux/macOS
   ./install_python.sh
   
   # Su Windows
   # Prima esegui: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install_python.sh
   ```

2. Lo script automaticamente:
   - Verifica che Python sia installato
   - Offre la possibilità di creare un ambiente virtuale
   - Installa tutte le dipendenze necessarie
   - Crea un file `.env` di esempio se non esiste

#### Metodo manuale
1. Crea un ambiente virtuale Python e attivalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   pip install fastapi uvicorn pydantic rich
   ```

3. Configura la chiave API DeepSeek:
   - Crea un file `.env` nella directory principale con la tua chiave API:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     DEEPSEEK_MODEL=deepseek-chat
     DEEPSEEK_API_BASE=https://api.deepseek.com/v1
     ```
   - Nota: Il file `.env` è incluso in `.gitignore` per evitare l'esposizione accidentale della chiave

## Utilizzo

### Avvio dell'EA
1. Carica l'EA su un grafico per uno dei simboli supportati
2. Configura i parametri:
   - BridgeMode: "FILE" (ponte predefinito basato su file)
   - RiskPercent: Percentuale di rischio per operazione (predefinito 1%)
   - Lots: Dimensione del lotto fissa (0 = calcolo automatico)
   - MagicNumber: Identificatore univoco per le operazioni
   - UseTrailingStop: Abilita/disabilita trailing stop
   - SignalCheckSeconds: Frequenza di controllo dei segnali
   - ExportOHLC: Abilita/disabilita esportazione dati OHLC
   - FilePath: Percorso per le operazioni sui file

### Avvio Semplificato (Raccomandato)

Utilizza lo script interattivo di controllo per avviare tutti i componenti Python con un'interfaccia user-friendly:

1. Avvia lo script di controllo:
   ```bash
   ./start_trading_bot.sh
   ```

2. Utilizza il menu interattivo per:
   - Avviare/arrestare tutti i servizi con un click
   - Avviare selettivamente il motore dei segnali, l'interfaccia chat o il server web
   - Generare grafici interattivi per le commodity
   - Controllare lo stato dei servizi
   - Visualizzare i log dei vari componenti

   ![Menu Interattivo](https://example.com/screenshots/menu.png)

3. Funzionalità principali:
   - **Avvio Automatizzato**: Gestisce l'ambiente virtuale e le dipendenze
   - **Monitoraggio Servizi**: Visualizza lo stato di tutti i componenti Python
   - **Generazione Grafici**: Interfaccia guidata per creare grafici interattivi
   - **Gestione Log**: Accesso facile ai log di tutti i componenti

### Avvio Manuale dei Componenti

1. Naviga alla directory principale del progetto:
   ```bash
   cd /path/to/OpenMT4TradingBot
   ```

2. Avvia il motore di segnali:
   ```bash
   python3 python/signal_engine.py
   ```

3. Opzioni disponibili:
   ```
   --mt4-path PATH     Percorso alla directory MT4 Files
   --data-path PATH    Percorso alla directory dei dati
   --backtest          Esegui backtest
   --update-cot        Aggiorna i dati COT ed esci
   --use-deepseek      Abilita l'integrazione con DeepSeek
   --compress=N        Imposta livello compressione cache (0-9, default: 6)
   --nocompress        Disabilita la compressione della cache
   ```

### Utilizzo dell'interfaccia chat

#### Server Web
1. Avvia il server web:
   ```bash
   python3 python/chat_interface.py --server --port 8000
   ```

2. Accedi all'API tramite browser:
   - Apri `http://localhost:8000` nel tuo browser

3. Oppure usa l'API REST:
   ```bash
   curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is the current bias on Gold?"}'
   ```

#### Interfaccia a Linea di Comando (CLI)
1. Fai una domanda direttamente:
   ```bash
   python3 python/chat_interface.py "Perché il bot ha chiuso la posizione long su WTI?"
   ```

2. Modalità interattiva:
   ```bash
   python3 python/chat_interface.py
   ```

3. Comandi speciali disponibili nell'interfaccia:
   - `/analyze [simbolo]` - Analizza i fattori di mercato
   - `/patterns [simbolo]` - Identifica pattern tecnici
   - `/news [simbolo]` - Mostra le ultime notizie
   - `/chart [simbolo] [periodo] [intervallo]` - Genera un grafico interattivo (es. `/chart XAUUSD 1y 1d`)
   - `/optimize` - Ottimizza il portafoglio
   - `/scenarios` - Analisi scenari di mercato

## File Structure

```
/OpenMT4TradingBot/              # Directory principale del progetto
  ├─ mql4/                     # Componenti MetaTrader 4
  │   └─ OpenMT4TradingBot.mq4 # Expert Advisor MT4 per l'esecuzione dei segnali di trading
  ├─ python/                   # Componenti Python del sistema
  │   ├─ signal_engine.py      # Motore principale per il calcolo dei segnali di trading
  │   ├─ deepseek_utils.py     # Utilities per l'integrazione con l'API DeepSeek
  │   ├─ chat_interface.py     # Interfaccia a riga di comando per comunicare con l'AI
  │   ├─ charting_utils.py     # Utilities per la generazione di grafici interattivi
  │   ├─ api_server.py         # Server API FastAPI per la comunicazione con la dashboard React
  │   ├─ requirements.txt      # Elenco delle dipendenze Python richieste
  │   └─ setup.py              # Script di configurazione per l'installazione
  ├─ web-dashboard/            # Interfaccia utente moderna basata su React
  │   ├─ package.json           # Configurazione del progetto React e dipendenze
  │   ├─ src/                   # Codice sorgente dell'applicazione React
  │   │   ├─ components/         # Componenti React modulari
  │   │   │   ├─ Dashboard.jsx     # Componente principale che organizza l'interfaccia
  │   │   │   ├─ TradingChart.jsx  # Grafico interattivo per visualizzare dati OHLC e segnali
  │   │   │   ├─ ApiUsageMonitor.jsx # Monitoraggio dell'utilizzo dell'API DeepSeek
  │   │   │   ├─ MarketOverview.jsx # Panoramica dei mercati con stato e filtri attivi
  │   │   │   ├─ SignalsTable.jsx   # Tabella dei segnali di trading con filtri
  │   │   │   └─ BotControls.jsx   # Controlli per avviare/fermare il bot e modificare le impostazioni
  │   │   ├─ pages/               # Pagine dell'applicazione React
  │   │   │   └─ index.jsx         # Pagina principale che carica il Dashboard
  │   │   ├─ styles/              # Fogli di stile CSS
  │   │   │   └─ styles.css        # Stile globale dell'applicazione
  │   │   ├─ api/                 # Funzioni per le chiamate API al backend
  │   │   ├─ hooks/               # Hook React personalizzati
  │   │   └─ utils/               # Funzioni di utilità condivise
  │   ├─ public/                # File statici pubblici (favicon, immagini, ecc.)
  │   └─ node_modules/          # Dipendenze JavaScript installate (generato automaticamente)
  ├─ data/                     # Dati utilizzati dal sistema
  │   ├─ cot.csv                # Dati COT (Commitment of Traders)
  │   ├─ season.json            # Configurazione della stagionalità per i vari mercati
  │   └─ signals.json           # File di output con i segnali di trading generati
  ├─ logs/                     # Directory per i file di log
  │   ├─ signal_engine.log      # Log del motore di segnali
  │   ├─ chat_interface.log     # Log dell'interfaccia chat
  │   ├─ api_server.log         # Log del server API
  │   └─ react_interface.log    # Log dell'interfaccia React
  ├─ install_python.sh         # Script per l'installazione dell'ambiente Python
  ├─ start_trading_bot.sh      # Script per avviare e gestire i componenti del trading bot
  ├─ start_dashboard.sh        # Script per avviare la dashboard React e il server API
  ├─ .env                      # File di configurazione per le variabili d'ambiente (API key)
  ├─ .gitignore                # Configurazione per escludere file dal controllo versione
  └─ README.md                # Documentazione del progetto
```

## Dettagli della Strategia

### Regole di Entrata
- **Entrata Long**: Chiusura di ieri uguale al massimo più alto degli ultimi 40 bar
- **Entrata Short**: Chiusura di ieri uguale al minimo più basso degli ultimi 40 bar

### Filtri
- **Filtro COT**:
  - Long solo se la posizione netta commerciale ≤ -1σ sotto la media di 3 anni
  - Short solo se la posizione netta commerciale ≥ +1σ sopra la media di 3 anni

- **Filtro Stagionale**:
  - Dimensionamento normale delle posizioni se la direzione dell'operazione corrisponde al bias stagionale
  - Dimensionamento dimezzato delle posizioni se la direzione dell'operazione contraddice il bias stagionale

### Regole di Uscita
- **Stop Loss**: 1,5 × ATR(20)
- **Take Profit**: 3,0 × ATR(20)
- **Trailing Stop**: Si aggiorna quando il prezzo si muove ≥ 1 ATR a favore

## Integrazione con DeepSeek AI

Il sistema include funzionalità potenziate dall'intelligenza artificiale attraverso l'API DeepSeek:

### Analisi del Sentimento delle Notizie
- Analizza i titoli delle notizie per determinare il bias di trading
- Può regolare il dimensionamento delle posizioni o saltare operazioni in base al sentimento
- Risposte memorizzate nella cache per minimizzare l'utilizzo dell'API

### Domande e Risposte in Linguaggio Naturale
- Interroga il tuo sistema di trading in linguaggio comune
- Esempi di domande:
  - "Perché il bot ha aperto una posizione long sull'oro?"
  - "Quali sono i dati COT attuali per l'argento?"
  - "Come sta andando il mio portafoglio questo mese?"

### Sicurezza della Chiave API
- Memorizza la tua chiave API DeepSeek nel file `.env`
- Questo file è escluso da Git per prevenire l'esposizione accidentale
- L'utilizzo del token è ottimizzato con un sistema di cache avanzato

### Ottimizzazioni Cache
- **Sistema di cache a due livelli**: Memoria (LRU) + Disco (JSON compresso)
- **Compressione GZIP**: Riduce spazio su disco fino al 70-80% per risposte API lunghe
- **Ottimizzazione delle chiavi di cache**:
  - Normalizzazione: elimina duplicati dovuti a case, spazi o caratteri speciali
  - Limitazione intelligente della lunghezza: tronca query lunghe mantenendo l'unicità
  - Organizzazione gerarchica: struttura ottimizzata in sottodirectory per tipo
  - Sharding dei file: distribuzione per evitare directory troppo popolate
- **TTL differenziati per tipo di dato**:
  - Chat responses: 10 minuti
  - Notizie: 1 ora
  - Analisi di mercato: 30 minuti
  - Riconoscimento pattern: 1 ora
  - Ottimizzazione portfolio: 20 minuti
  - Analisi di scenario: 30 minuti
- **Gestione automatica dello spazio**: Pulizia file scaduti e compressione adattiva quando lo spazio scarseggia

## Testing

### MT4 Strategy Tester
1. Apri MT4 Strategy Tester
2. Seleziona l'EA
3. Configura le impostazioni:
   - Modello: "Solo prezzi di apertura" o "Ogni tick"
   - Usa intervallo di date che copra diversi cicli stagionali
   - Modalità visuale per analisi dettagliata

### Python Backtest
Esegui la funzione di backtest integrata:
```
python signal_engine.py --backtest
```

## Nuove Funzionalità

### Dashboard React Moderna

Abbiamo implementato una dashboard web moderna basata su React per monitorare e controllare il trading bot in tempo reale:

- **Interfaccia Responsive**: Design moderno che si adatta a dispositivi desktop e mobile
- **Grafici Interattivi**: Visualizzazione professionale di candlestick OHLC con indicatori Donchian
- **Monitoraggio API DeepSeek**: Visualizzazione in tempo reale dell'utilizzo e del throttling dell'API
- **Panoramica Mercati**: Stato attivo/inattivo di tutti i mercati supportati con filtri e segnali
- **Tabella Segnali**: Visualizzazione dettagliata dei segnali di trading con filtri e ordinamento
- **Controlli Bot**: Interfaccia per avviare/fermare il bot e configurare limiti di costo e soglie di throttling

Per avviare la dashboard, utilizzare il nuovo script `start_dashboard.sh`:

```bash
./start_dashboard.sh
```

### Grafici Interattivi per Commodity

Abbiamo integrato la visualizzazione di grafici interattivi per le commodity supportate:

- **Candlestick Charts**: Visualizzazione professionale dei dati OHLC
- **Indicatore di Volume**: Analisi del volume di trading integrata
- **Interattività**: Zoom, pan, e hover per analisi dettagliata
- **Timeframes Flessibili**: Da intraday a dati pluriennali
- **Accesso Multi-Piattaforma**:
  - Tramite interfaccia chat (`/chart XAUUSD 1y 1d`)
  - Attraverso il menu interattivo di `start_trading_bot.sh`
  - Direttamente tramite `charting_utils.py`
  - Nella nuova dashboard React (`start_dashboard.sh`)

### Interfaccia di Controllo Centralizzata

Il nuovo script `start_trading_bot.sh` fornisce un pannello di controllo unificato:

- **Menu Interattivo**: Semplice da usare anche per utenti non tecnici
- **Monitoraggio in Tempo Reale**: Visualizzazione dello stato di tutti i servizi
- **Gestione Log Centralizzata**: Accesso immediato ai log di tutti i componenti
- **Generazione Guidata dei Grafici**: Procedura guidata per generare grafici interattivi

## TODO e Miglioramenti Futuri

- Aggiungere analisi COT più sofisticate
- Implementare machine learning per parametri adattivi
- Aggiungere gestione del rischio a livello di portafoglio
- Supporto per più strumenti di trading
- Aggiungere test unitari per tutti i componenti
- Implementare cache distribuita per deployment multi-istanza
- Aggiungere dashboard di metriche cache per monitoraggio delle prestazioni
- Migliorare i grafici con overlay di indicatori tecnici
- Creare una GUI desktop nativa utilizzando PyQt o simili
- Aggiungere WebSocket per aggiornamenti in tempo reale nella dashboard
- Aggiungere autenticazione e sicurezza per l'accesso alla dashboard

## Licenza

Licenza MIT

Copyright (c) 2025 Immaginet Srl

È concessa, gratuitamente, a chiunque ottenga una copia
di questo software e dei file di documentazione associati (il "Software"), l'autorizzazione
a utilizzare il Software senza restrizioni, inclusi, senza limitazione, i diritti
di utilizzare, copiare, modificare, unire, pubblicare, distribuire, concedere in sublicenza e/o vendere
copie del Software, e di permettere alle persone a cui il Software è
fornito di farlo, alle seguenti condizioni:

L'avviso di copyright sopra indicato e questo avviso di autorizzazione devono essere inclusi in tutte
le copie o parti sostanziali del Software.

IL SOFTWARE VIENE FORNITO "COSÌ COM'È", SENZA GARANZIA DI ALCUN TIPO, ESPRESSA O
IMPLICITA, INCLUSE, MA NON SOLO, LE GARANZIE DI COMMERCIABILITÀ,
IDONEITÀ PER UN PARTICOLARE SCOPO E NON VIOLAZIONE. IN NESSUN CASO GLI
AUTORI O I TITOLARI DEL COPYRIGHT SARANNO RESPONSABILI PER QUALSIASI RECLAMO, DANNO O ALTRA
RESPONSABILITÀ, SIA IN UN'AZIONE DI CONTRATTO, TORTO O ALTRIMENTI, DERIVANTE DA,
FUORI O IN CONNESSIONE CON IL SOFTWARE O L'USO O ALTRE OPERAZIONI NEL
SOFTWARE.