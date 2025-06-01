import React from 'react';
import dynamic from 'next/dynamic';

// Importazione dinamica di Plotly per evitare problemi di SSR
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const ApiUsageMonitor = ({ apiUsage }) => {
  const { daily, monthly, throttling, active_markets } = apiUsage;
  
  // Calcola il colore in base al livello di throttling
  const getThrottlingColor = (level) => {
    switch(level) {
      case 'normal': return '#4caf50';
      case 'light': return '#8bc34a';
      case 'moderate': return '#ffc107';
      case 'heavy': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#4caf50';
    }
  };
  
  // Calcola la percentuale di utilizzo del limite giornaliero
  const dailyUsagePercent = daily?.percent_of_limit || 0;
  const throttlingColor = getThrottlingColor(throttling?.current_level || 'normal');
  
  // Crea il grafico a gauge per mostrare l'utilizzo giornaliero
  const gaugeData = [{
    type: 'indicator',
    mode: 'gauge+number',
    value: dailyUsagePercent,
    title: { text: 'Utilizzo API giornaliero', font: { size: 14 } },
    gauge: {
      axis: { range: [0, 100], tickwidth: 1 },
      bar: { color: throttlingColor },
      bgcolor: 'white',
      borderwidth: 2,
      bordercolor: 'gray',
      steps: [
        { range: [0, 20], color: 'rgba(76, 175, 80, 0.3)' },
        { range: [20, 40], color: 'rgba(139, 195, 74, 0.3)' },
        { range: [40, 60], color: 'rgba(255, 193, 7, 0.3)' },
        { range: [60, 80], color: 'rgba(255, 152, 0, 0.3)' },
        { range: [80, 100], color: 'rgba(244, 67, 54, 0.3)' }
      ],
      threshold: {
        line: { color: 'red', width: 2 },
        thickness: 0.75,
        value: 90
      }
    }
  }];
  
  const gaugeLayout = {
    width: 300,
    height: 200,
    margin: { t: 25, r: 25, l: 25, b: 25 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: { color: 'darkblue', family: 'Arial' }
  };
  
  return (
    <div className="api-usage-monitor">
      <h2>Monitoraggio API DeepSeek</h2>
      
      <div className="usage-stats">
        <div className="gauge-chart">
          <Plot
            data={gaugeData}
            layout={gaugeLayout}
            config={{ displayModeBar: false }}
          />
        </div>
        
        <div className="usage-details">
          <div className="detail-item">
            <span className="label">Costo giornaliero:</span>
            <span className="value">${daily?.estimated_cost?.toFixed(2) || '0.00'}</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Token utilizzati oggi:</span>
            <span className="value">{daily?.total_tokens?.toLocaleString() || '0'}</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Richieste oggi:</span>
            <span className="value">{daily?.requests_count || '0'}</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Costo mensile:</span>
            <span className="value">${monthly?.estimated_cost?.toFixed(2) || '0.00'}</span>
          </div>
          
          <div className="detail-item throttling-level">
            <span className="label">Livello throttling:</span>
            <span 
              className="value" 
              style={{ color: throttlingColor, fontWeight: 'bold' }}
            >
              {throttling?.current_level || 'normal'}
            </span>
          </div>
        </div>
      </div>
      
      <div className="active-markets">
        <h3>Mercati attivi ({active_markets?.length || 0})</h3>
        <div className="markets-list">
          {active_markets && active_markets.length > 0 ? (
            active_markets.map((market, index) => (
              <span key={index} className="market-badge">{market}</span>
            ))
          ) : (
            <p className="no-markets">Nessun mercato attivo</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiUsageMonitor;
