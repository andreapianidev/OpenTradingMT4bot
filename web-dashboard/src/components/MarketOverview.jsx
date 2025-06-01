import React from 'react';

const MarketOverview = ({ activeMarkets, signals, onSelectSymbol, selectedSymbol }) => {
  // Lista completa dei simboli supportati
  const allSymbols = [
    "XAUUSD", "XAGUSD", "WTICOUSD", "BCOUSD", 
    "NATGASUSD", "CORNUSD", "SOYBNUSD", "WHEATUSD"
  ];
  
  // Determina lo stato di ogni mercato
  const getMarketStatus = (symbol) => {
    // Controlla se il mercato è attivo
    const isActive = activeMarkets?.includes(symbol);
    
    // Controlla se c'è un segnale per questo simbolo
    const signal = signals?.[symbol];
    let signalType = signal?.signal || 'neutral';
    
    return {
      isActive,
      signalType,
      direction: signal?.direction || 'neutral',
      confidence: signal?.confidence || 0
    };
  };
  
  // Icona per il tipo di segnale
  const getSignalIcon = (signalType) => {
    switch(signalType) {
      case 'buy':
        return <span className="signal-icon buy">▲</span>;
      case 'sell':
        return <span className="signal-icon sell">▼</span>;
      default:
        return <span className="signal-icon neutral">■</span>;
    }
  };
  
  // Classe CSS per il tipo di segnale
  const getSignalClass = (signalType) => {
    switch(signalType) {
      case 'buy':
        return 'buy-signal';
      case 'sell':
        return 'sell-signal';
      default:
        return 'neutral-signal';
    }
  };
  
  return (
    <div className="market-overview">
      <h2>Panoramica Mercati</h2>
      
      <div className="markets-grid">
        {allSymbols.map(symbol => {
          const { isActive, signalType, direction, confidence } = getMarketStatus(symbol);
          
          return (
            <div 
              key={symbol}
              className={`market-card ${isActive ? 'active' : 'inactive'} ${selectedSymbol === symbol ? 'selected' : ''}`}
              onClick={() => onSelectSymbol(symbol)}
            >
              <div className="market-header">
                <h3 className="symbol">{symbol}</h3>
                <span className={`status-badge ${isActive ? 'active' : 'inactive'}`}>
                  {isActive ? 'Attivo' : 'Inattivo'}
                </span>
              </div>
              
              <div className={`signal-indicator ${getSignalClass(signalType)}`}>
                {getSignalIcon(signalType)}
                <span className="signal-text">{signalType.toUpperCase()}</span>
              </div>
              
              {signalType !== 'neutral' && (
                <div className="signal-details">
                  <div className="confidence-bar">
                    <div 
                      className="confidence-level"
                      style={{ width: `${confidence * 100}%` }}
                    ></div>
                  </div>
                  <span className="confidence-text">{(confidence * 100).toFixed(0)}% confidenza</span>
                </div>
              )}
              
              <div className="market-filters">
                {signals?.[symbol]?.cot_favorable !== undefined && (
                  <span className={`filter-badge cot ${signals[symbol].cot_favorable ? 'favorable' : 'unfavorable'}`}>
                    COT
                  </span>
                )}
                
                {signals?.[symbol]?.season_favorable !== undefined && (
                  <span className={`filter-badge season ${signals[symbol].season_favorable ? 'favorable' : 'unfavorable'}`}>
                    Stagionale
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MarketOverview;
