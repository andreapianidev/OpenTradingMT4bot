import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Dizionario di mapping per i simboli delle commodity più comuni su Yahoo Finance
# Questo potrebbe aver bisogno di aggiustamenti a seconda della fonte esatta e del formato dei simboli
COMMODITY_SYMBOLS_YFINANCE = {
    "XAUUSD": "GC=F",  # Oro
    "XAGUSD": "SI=F",  # Argento
    "WTICOUSD": "CL=F", # Petrolio WTI
    "BCOUSD": "BZ=F",  # Petrolio Brent
    "NATGASUSD": "NG=F",# Gas Naturale
    "CORNUSD": "ZC=F",  # Mais
    "SOYBNUSD": "ZS=F", # Soia
    "WHEATUSD": "KE=F", # Grano
    # Aggiungi altri simboli se necessario
}

def get_commodity_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Scarica i dati storici per una commodity da Yahoo Finance.

    Args:
        symbol (str): Il simbolo della commodity (es. "XAUUSD", "WTICOUSD").
        period (str, optional): Il periodo per cui scaricare i dati (es. "1mo", "1y", "5y", "max"). Default "1y".
        interval (str, optional): L'intervallo dei dati (es. "1d", "1wk", "1mo"). Default "1d".

    Returns:
        pd.DataFrame: DataFrame con i dati OHLCV, o None se il simbolo non è valido o si verifica un errore.
    """
    yf_symbol = COMMODITY_SYMBOLS_YFINANCE.get(symbol.upper())
    if not yf_symbol:
        print(f"Simbolo {symbol} non mappato per Yahoo Finance. Controlla COMMODITY_SYMBOLS_YFINANCE.")
        # Prova a usare il simbolo direttamente se non è nel mapping, potrebbe funzionare per alcuni casi
        yf_symbol = symbol.upper()
        # Considera di aggiungere qui un avviso o un log se il simbolo non è nel mapping predefinito

    try:
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(period=period, interval=interval)
        if data.empty:
            print(f"Nessun dato trovato per il simbolo {yf_symbol} ({symbol}) con periodo {period} e intervallo {interval}.")
            return None
        # Rinomina le colonne per coerenza se necessario (yfinance di solito le ha già corrette)
        data.rename(columns={
            "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
        }, inplace=True)
        return data[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"Errore durante il download dei dati per {yf_symbol} ({symbol}): {e}")
        return None

def plot_candlestick_chart(df: pd.DataFrame, symbol_display: str = "Commodity") -> go.Figure:
    """Genera un grafico a candele interattivo con Plotly.

    Args:
        df (pd.DataFrame): DataFrame con i dati OHLCV (colonne 'open', 'high', 'low', 'close', 'volume').
                           L'indice deve essere di tipo Datetime.
        symbol_display (str, optional): Nome del simbolo da visualizzare nel titolo del grafico. Default "Commodity".

    Returns:
        go.Figure: Oggetto figura di Plotly.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            raise ValueError(f"L'indice del DataFrame deve essere convertibile in DatetimeIndex. Errore: {e}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, subplot_titles=(f'{symbol_display} Candlestick', 'Volume'),
                        row_width=[0.2, 0.7])

    # Grafico a candele
    fig.add_trace(go.Candlestick(x=df.index,
                               open=df['open'],
                               high=df['high'],
                               low=df['low'],
                               close=df['close'],
                               name="OHLC"), row=1, col=1)

    # Grafico del volume
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], name="Volume", marker_color='rgba(0,0,100,0.6)'), row=2, col=1)

    fig.update_layout(
        title_text=f"{symbol_display} Prezzo e Volume",
        xaxis_title="Data",
        yaxis_title="Prezzo",
        xaxis_rangeslider_visible=False, # Nasconde il range slider di default sotto il grafico principale
        legend_title_text="Legenda",
        template="plotly_white"
    )
    
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig

if __name__ == '__main__':
    # Esempio di utilizzo
    print("Esempio di utilizzo di charting_utils:")
    
    # Scarica dati per l'oro (XAUUSD)
    gold_symbol = "XAUUSD"
    print(f"\nRecupero dati per {gold_symbol}...")
    gold_data = get_commodity_data(gold_symbol, period="6mo", interval="1d")
    
    if gold_data is not None and not gold_data.empty:
        print(f"Dati per {gold_symbol} recuperati:")
        print(gold_data.head())
        
        # Genera e mostra il grafico
        print(f"\nGenerazione grafico per {gold_symbol}...")
        fig_gold = plot_candlestick_chart(gold_data, symbol_display=gold_symbol)
        # Per visualizzare il grafico in un ambiente interattivo (es. Jupyter Notebook o script locale):
        fig_gold.show() 
        print(f"Grafico per {gold_symbol} generato. Se eseguito come script, dovrebbe aprirsi una finestra del browser.")
        
        # Esempio di salvataggio in HTML (utile per l'integrazione)
        html_file_gold = f"{gold_symbol}_chart.html"
        fig_gold.write_html(html_file_gold)
        print(f"Grafico salvato come {html_file_gold}")
    else:
        print(f"Non è stato possibile recuperare o graficare i dati per {gold_symbol}.")

    # Esempio per una commodity che potrebbe non essere nel mapping diretto o fallire
    oil_symbol = "WTICOUSD"
    print(f"\nRecupero dati per {oil_symbol}...")
    oil_data = get_commodity_data(oil_symbol, period="3mo")
    if oil_data is not None and not oil_data.empty:
        print(f"Dati per {oil_symbol} recuperati.")
        fig_oil = plot_candlestick_chart(oil_data, symbol_display=oil_symbol)
        fig_oil.show()
        html_file_oil = f"{oil_symbol}_chart.html"
        fig_oil.write_html(html_file_oil)
        print(f"Grafico per {oil_symbol} generato e salvato come {html_file_oil}.")
    else:
        print(f"Non è stato possibile recuperare o graficare i dati per {oil_symbol}.")
