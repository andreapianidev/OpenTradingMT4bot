import React, { useState } from 'react';

const SignalsTable = ({ signals }) => {
  const [filterType, setFilterType] = useState('all'); // 'all', 'buy', 'sell', 'neutral'
  
  // Converti i segnali in un array per facilitare il filtraggio e l'ordinamento
  const signalsArray = Object.entries(signals || {}).map(([symbol, data]) => ({
    symbol,
    ...data
  }));
  
  // Filtra in base al tipo di segnale
  const filteredSignals = signalsArray.filter(signal => {
    if (filterType === 'all') return true;
    return signal.signal === filterType;
  });
  
  // Ordina i segnali: prima i non-neutrali, poi per confidenza
  const sortedSignals = [...filteredSignals].sort((a, b) => {
    // Prima metti i segnali non neutrali
    if (a.signal !== 'neutral' && b.signal === 'neutral') return -1;
    if (a.signal === 'neutral' && b.signal !== 'neutral') return 1;
    
    // Poi ordina per confidenza (se disponibile)
    if (a.confidence && b.confidence) {
      return b.confidence - a.confidence;
    }
    
    // Infine ordina per nome simbolo
    return a.symbol.localeCompare(b.symbol);
  });
  
  // Formatta la data in modo leggibile
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <div className="signals-table-container">
      <div className="signals-header">
        <h2>Segnali di Trading</h2>
        
        <div className="signals-filter">
          <button 
            className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            Tutti
          </button>
          <button 
            className={`filter-btn buy ${filterType === 'buy' ? 'active' : ''}`}
            onClick={() => setFilterType('buy')}
          >
            Acquisto
          </button>
          <button 
            className={`filter-btn sell ${filterType === 'sell' ? 'active' : ''}`}
            onClick={() => setFilterType('sell')}
          >
            Vendita
          </button>
          <button 
            className={`filter-btn neutral ${filterType === 'neutral' ? 'active' : ''}`}
            onClick={() => setFilterType('neutral')}
          >
            Neutrali
          </button>
        </div>
      </div>
      
      <div className="signals-table-wrapper">
        <table className="signals-table">
          <thead>
            <tr>
              <th>Simbolo</th>
              <th>Segnale</th>
              <th>Direzione</th>
              <th>Confidenza</th>
              <th>Filtro COT</th>
              <th>Filtro Stagionale</th>
              <th>Prezzo Entry</th>
              <th>Stop Loss</th>
              <th>Take Profit</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {sortedSignals.length > 0 ? (
              sortedSignals.map((signal) => (
                <tr key={signal.symbol} className={`signal-row ${signal.signal}`}>
                  <td className="symbol-cell">{signal.symbol}</td>
                  <td className={`signal-cell ${signal.signal}`}>
                    {signal.signal === 'buy' && '▲ ACQUISTO'}
                    {signal.signal === 'sell' && '▼ VENDITA'}
                    {signal.signal === 'neutral' && '■ NEUTRALE'}
                  </td>
                  <td>{signal.direction || 'N/A'}</td>
                  <td>
                    {signal.confidence ? (
                      <div className="confidence-wrapper">
                        <div className="confidence-bar">
                          <div 
                            className={`confidence-fill ${signal.signal}`}
                            style={{ width: `${signal.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span>{(signal.confidence * 100).toFixed(0)}%</span>
                      </div>
                    ) : 'N/A'}
                  </td>
                  <td className={signal.cot_favorable ? 'favorable' : 'unfavorable'}>
                    {signal.cot_favorable !== undefined ? (signal.cot_favorable ? 'Favorevole' : 'Sfavorevole') : 'N/A'}
                  </td>
                  <td className={signal.season_favorable ? 'favorable' : 'unfavorable'}>
                    {signal.season_favorable !== undefined ? (signal.season_favorable ? 'Favorevole' : 'Sfavorevole') : 'N/A'}
                  </td>
                  <td>{signal.entry ? signal.entry.toFixed(2) : 'N/A'}</td>
                  <td>{signal.sl ? signal.sl.toFixed(2) : 'N/A'}</td>
                  <td>{signal.tp ? signal.tp.toFixed(2) : 'N/A'}</td>
                  <td>{formatDate(signal.timestamp)}</td>
                </tr>
              ))
            ) : (
              <tr className="no-signals">
                <td colSpan="10">Nessun segnale disponibile</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SignalsTable;
