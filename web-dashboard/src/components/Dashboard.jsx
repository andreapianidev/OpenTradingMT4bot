import React, { useState, useEffect } from 'react';
import TradingChart from './TradingChart';
import MarketOverview from './MarketOverview';
import ApiUsageMonitor from './ApiUsageMonitor';
import SignalsTable from './SignalsTable';
import BotControls from './BotControls';

const Dashboard = () => {
  const [activeMarkets, setActiveMarkets] = useState([]);
  const [signals, setSignals] = useState({});
  const [apiUsage, setApiUsage] = useState({
    daily: { total_tokens: 0, estimated_cost: 0, percent_of_limit: 0 },
    throttling: { current_level: 'normal' }
  });
  const [selectedSymbol, setSelectedSymbol] = useState('XAUUSD');
  
  // Fetch active markets
  useEffect(() => {
    const fetchActiveMarkets = async () => {
      try {
        const response = await fetch('/api/active-markets');
        const data = await response.json();
        setActiveMarkets(data.markets || []);
      } catch (error) {
        console.error('Error fetching active markets:', error);
      }
    };
    
    fetchActiveMarkets();
    const interval = setInterval(fetchActiveMarkets, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);
  
  // Fetch signals
  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await fetch('/api/signals');
        const data = await response.json();
        setSignals(data);
      } catch (error) {
        console.error('Error fetching signals:', error);
      }
    };
    
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  // Fetch API usage
  useEffect(() => {
    const fetchApiUsage = async () => {
      try {
        const response = await fetch('/api/usage');
        const data = await response.json();
        setApiUsage(data);
      } catch (error) {
        console.error('Error fetching API usage:', error);
      }
    };
    
    fetchApiUsage();
    const interval = setInterval(fetchApiUsage, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>OpenMT4TradingBot Dashboard</h1>
        <div className="throttling-indicator">
          <span className={`throttling-badge ${apiUsage.throttling.current_level}`}>
            API Throttling: {apiUsage.throttling.current_level}
          </span>
          <span className="cost-badge">
            Daily Cost: ${apiUsage.daily.estimated_cost.toFixed(2)} ({apiUsage.daily.percent_of_limit.toFixed(1)}%)
          </span>
        </div>
      </header>
      
      <div className="dashboard-content">
        <div className="left-panel">
          <MarketOverview 
            activeMarkets={activeMarkets} 
            signals={signals}
            onSelectSymbol={setSelectedSymbol}
            selectedSymbol={selectedSymbol}
          />
          <ApiUsageMonitor apiUsage={apiUsage} />
        </div>
        
        <div className="main-panel">
          <TradingChart symbol={selectedSymbol} />
          <SignalsTable signals={signals} />
        </div>
        
        <div className="right-panel">
          <BotControls />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
