import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

// Importazione dinamica di Plotly per evitare problemi di SSR
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const TradingChart = ({ symbol }) => {
  const [chartData, setChartData] = useState(null);
  const [timeframe, setTimeframe] = useState('1d');
  const [indicator, setIndicator] = useState('donchian');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChartData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/chart-data?symbol=${symbol}&timeframe=${timeframe}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch chart data: ${response.statusText}`);
        }
        
        const data = await response.json();
        setChartData(data);
      } catch (err) {
        console.error('Error fetching chart data:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchChartData();
    // Aggiornamento ogni 5 minuti
    const interval = setInterval(fetchChartData, 300000);
    
    return () => clearInterval(interval);
  }, [symbol, timeframe]);

  const renderPlot = () => {
    if (isLoading) {
      return <div className="chart-loading">Caricamento grafico...</div>;
    }
    
    if (error) {
      return <div className="chart-error">Errore: {error}</div>;
    }
    
    if (!chartData || !chartData.ohlc || chartData.ohlc.length === 0) {
      return <div className="chart-no-data">Nessun dato disponibile per {symbol}</div>;
    }

    // Configurazione del grafico OHLC principale
    const candlestickTrace = {
      x: chartData.dates,
      open: chartData.ohlc.map(d => d.open),
      high: chartData.ohlc.map(d => d.high),
      low: chartData.ohlc.map(d => d.low),
      close: chartData.ohlc.map(d => d.close),
      type: 'candlestick',
      name: symbol,
      increasing: {line: {color: '#26a69a'}},
      decreasing: {line: {color: '#ef5350'}}
    };
    
    // Array di tracce per il grafico
    const traces = [candlestickTrace];
    
    // Aggiungi indicatori in base alla selezione
    if (indicator === 'donchian' && chartData.donchian) {
      traces.push({
        x: chartData.dates,
        y: chartData.donchian.upper,
        type: 'scatter',
        mode: 'lines',
        name: 'Donchian Upper',
        line: {color: 'rgba(33, 150, 243, 0.7)'}
      });
      
      traces.push({
        x: chartData.dates,
        y: chartData.donchian.lower,
        type: 'scatter',
        mode: 'lines',
        name: 'Donchian Lower',
        line: {color: 'rgba(33, 150, 243, 0.7)'},
        fill: 'tonexty',
        fillcolor: 'rgba(33, 150, 243, 0.1)'
      });
    }
    
    // Aggiungi segnali di trading se disponibili
    if (chartData.signals && chartData.signals.length > 0) {
      const buySignals = chartData.signals
        .filter(s => s.type === 'buy')
        .map(s => ({
          x: [s.date],
          y: [s.price],
          type: 'scatter',
          mode: 'markers',
          name: 'Buy Signal',
          marker: {
            color: 'green',
            size: 10,
            symbol: 'triangle-up'
          }
        }));
      
      const sellSignals = chartData.signals
        .filter(s => s.type === 'sell')
        .map(s => ({
          x: [s.date],
          y: [s.price],
          type: 'scatter',
          mode: 'markers',
          name: 'Sell Signal',
          marker: {
            color: 'red',
            size: 10,
            symbol: 'triangle-down'
          }
        }));
      
      traces.push(...buySignals, ...sellSignals);
    }
    
    const layout = {
      title: `${symbol} - ${timeframe}`,
      dragmode: 'zoom',
      showlegend: true,
      xaxis: {
        rangeslider: {
          visible: false
        },
        type: 'date'
      },
      yaxis: {
        autorange: true,
        title: 'Prezzo'
      },
      margin: {
        l: 50,
        r: 20,
        t: 40,
        b: 40
      },
      height: 500,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: [
        'lasso2d', 
        'select2d',
        'toggleSpikelines'
      ]
    };
    
    return (
      <Plot
        data={traces}
        layout={layout}
        config={config}
        className="trading-chart"
      />
    );
  };

  return (
    <div className="chart-container">
      <div className="chart-controls">
        <div className="timeframe-selector">
          <label htmlFor="timeframe">Timeframe:</label>
          <select 
            id="timeframe" 
            value={timeframe} 
            onChange={(e) => setTimeframe(e.target.value)}
          >
            <option value="1h">1 Ora</option>
            <option value="4h">4 Ore</option>
            <option value="1d">Giornaliero</option>
            <option value="1w">Settimanale</option>
          </select>
        </div>
        
        <div className="indicator-selector">
          <label htmlFor="indicator">Indicatore:</label>
          <select 
            id="indicator" 
            value={indicator} 
            onChange={(e) => setIndicator(e.target.value)}
          >
            <option value="donchian">Donchian Channel</option>
            <option value="atr">ATR</option>
            <option value="none">Nessuno</option>
          </select>
        </div>
      </div>
      
      {renderPlot()}
    </div>
  );
};

export default TradingChart;
