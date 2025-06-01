import React, { useState, useEffect } from 'react';

const BotControls = () => {
  const [botStatus, setBotStatus] = useState('disconnected'); // 'running', 'stopped', 'disconnected'
  const [engineStatus, setEngineStatus] = useState('disconnected');
  const [chatStatus, setChatStatus] = useState('disconnected');
  const [deepSeekEnabled, setDeepSeekEnabled] = useState(false);
  const [dailyLimit, setDailyLimit] = useState(5.0);
  const [throttlingConfig, setThrottlingConfig] = useState({
    normal_threshold: 0.2,
    light_threshold: 0.4,
    moderate_threshold: 0.6,
    heavy_threshold: 0.8,
    inactive_market_multiplier: 2.0
  });
  
  // Carica lo stato iniziale all'avvio
  useEffect(() => {
    const fetchBotStatus = async () => {
      try {
        const response = await fetch('/api/bot-status');
        const data = await response.json();
        
        setBotStatus(data.status || 'disconnected');
        setEngineStatus(data.engine_status || 'disconnected');
        setChatStatus(data.chat_status || 'disconnected');
        setDeepSeekEnabled(data.deepseek_enabled || false);
        setDailyLimit(data.daily_limit || 5.0);
        
        if (data.throttling_config) {
          setThrottlingConfig(data.throttling_config);
        }
      } catch (error) {
        console.error('Error fetching bot status:', error);
        setBotStatus('disconnected');
      }
    };
    
    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  // Funzione per avviare il bot
  const startBot = async () => {
    try {
      const response = await fetch('/api/bot-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'start' })
      });
      
      const data = await response.json();
      if (data.success) {
        setBotStatus('running');
      }
    } catch (error) {
      console.error('Error starting bot:', error);
    }
  };
  
  // Funzione per fermare il bot
  const stopBot = async () => {
    try {
      const response = await fetch('/api/bot-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'stop' })
      });
      
      const data = await response.json();
      if (data.success) {
        setBotStatus('stopped');
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
    }
  };
  
  // Funzione per aggiornare il limite giornaliero
  const updateDailyLimit = async () => {
    try {
      const response = await fetch('/api/update-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          daily_limit: dailyLimit,
          deepseek_enabled: deepSeekEnabled
        })
      });
      
      await response.json();
    } catch (error) {
      console.error('Error updating config:', error);
    }
  };
  
  // Funzione per aggiornare la configurazione di throttling
  const updateThrottlingConfig = async () => {
    try {
      const response = await fetch('/api/update-throttling', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(throttlingConfig)
      });
      
      await response.json();
    } catch (error) {
      console.error('Error updating throttling config:', error);
    }
  };
  
  // Gestisce il cambio dei valori di input
  const handleInputChange = (e, setter) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : parseFloat(e.target.value);
    setter(value);
  };
  
  // Gestisce il cambio dei valori di throttling
  const handleThrottlingChange = (e, key) => {
    const value = parseFloat(e.target.value);
    setThrottlingConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  const getStatusClass = (status) => {
    switch(status) {
      case 'running': return 'status-running';
      case 'stopped': return 'status-stopped';
      default: return 'status-disconnected';
    }
  };
  
  return (
    <div className="bot-controls">
      <h2>Controlli Bot</h2>
      
      <div className="status-panel">
        <div className={`status-indicator ${getStatusClass(botStatus)}`}>
          <span className="status-label">Stato Bot:</span>
          <span className="status-value">
            {botStatus === 'running' && 'In esecuzione'}
            {botStatus === 'stopped' && 'Fermato'}
            {botStatus === 'disconnected' && 'Disconnesso'}
          </span>
        </div>
        
        <div className={`status-indicator ${getStatusClass(engineStatus)}`}>
          <span className="status-label">Signal Engine:</span>
          <span className="status-value">
            {engineStatus === 'running' && 'In esecuzione'}
            {engineStatus === 'stopped' && 'Fermato'}
            {engineStatus === 'disconnected' && 'Disconnesso'}
          </span>
        </div>
        
        <div className={`status-indicator ${getStatusClass(chatStatus)}`}>
          <span className="status-label">Chat Interface:</span>
          <span className="status-value">
            {chatStatus === 'running' && 'In esecuzione'}
            {chatStatus === 'stopped' && 'Fermato'}
            {chatStatus === 'disconnected' && 'Disconnesso'}
          </span>
        </div>
      </div>
      
      <div className="control-buttons">
        <button 
          className="start-button"
          onClick={startBot}
          disabled={botStatus === 'running'}
        >
          Avvia Bot
        </button>
        
        <button 
          className="stop-button"
          onClick={stopBot}
          disabled={botStatus !== 'running'}
        >
          Ferma Bot
        </button>
      </div>
      
      <div className="settings-panel">
        <h3>Impostazioni DeepSeek API</h3>
        
        <div className="setting-item">
          <label className="toggle-switch">
            <input 
              type="checkbox" 
              checked={deepSeekEnabled} 
              onChange={(e) => handleInputChange(e, setDeepSeekEnabled)}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="setting-label">Abilita DeepSeek AI</span>
        </div>
        
        <div className="setting-item">
          <label>Limite Giornaliero ($):</label>
          <div className="input-with-buttons">
            <button 
              className="decrement-button"
              onClick={() => setDailyLimit(prev => Math.max(1, prev - 1))}
            >
              -
            </button>
            <input 
              type="number" 
              min="1" 
              step="0.5" 
              value={dailyLimit} 
              onChange={(e) => handleInputChange(e, setDailyLimit)}
            />
            <button 
              className="increment-button"
              onClick={() => setDailyLimit(prev => prev + 1)}
            >
              +
            </button>
          </div>
        </div>
        
        <button 
          className="update-button"
          onClick={updateDailyLimit}
        >
          Aggiorna Impostazioni
        </button>
      </div>
      
      <div className="throttling-panel">
        <h3>Configurazione Throttling</h3>
        
        <div className="throttling-sliders">
          <div className="slider-item">
            <label>Normale ({(throttlingConfig.normal_threshold * 100).toFixed(0)}%):</label>
            <input 
              type="range" 
              min="0.1" 
              max="0.3" 
              step="0.05" 
              value={throttlingConfig.normal_threshold} 
              onChange={(e) => handleThrottlingChange(e, 'normal_threshold')}
            />
          </div>
          
          <div className="slider-item">
            <label>Leggero ({(throttlingConfig.light_threshold * 100).toFixed(0)}%):</label>
            <input 
              type="range" 
              min="0.3" 
              max="0.5" 
              step="0.05" 
              value={throttlingConfig.light_threshold} 
              onChange={(e) => handleThrottlingChange(e, 'light_threshold')}
            />
          </div>
          
          <div className="slider-item">
            <label>Moderato ({(throttlingConfig.moderate_threshold * 100).toFixed(0)}%):</label>
            <input 
              type="range" 
              min="0.5" 
              max="0.7" 
              step="0.05" 
              value={throttlingConfig.moderate_threshold} 
              onChange={(e) => handleThrottlingChange(e, 'moderate_threshold')}
            />
          </div>
          
          <div className="slider-item">
            <label>Pesante ({(throttlingConfig.heavy_threshold * 100).toFixed(0)}%):</label>
            <input 
              type="range" 
              min="0.7" 
              max="0.9" 
              step="0.05" 
              value={throttlingConfig.heavy_threshold} 
              onChange={(e) => handleThrottlingChange(e, 'heavy_threshold')}
            />
          </div>
          
          <div className="slider-item">
            <label>Moltiplicatore Mercati Inattivi (x{throttlingConfig.inactive_market_multiplier.toFixed(1)}):</label>
            <input 
              type="range" 
              min="1.0" 
              max="5.0" 
              step="0.5" 
              value={throttlingConfig.inactive_market_multiplier} 
              onChange={(e) => handleThrottlingChange(e, 'inactive_market_multiplier')}
            />
          </div>
        </div>
        
        <button 
          className="update-button"
          onClick={updateThrottlingConfig}
        >
          Aggiorna Throttling
        </button>
      </div>
    </div>
  );
};

export default BotControls;
