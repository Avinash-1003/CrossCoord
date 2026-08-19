import React from 'react';

function FedAvgGraph({ syncs }) {
  // We'll simulate a line graph just using some CSS blocks for the visual effect
  // of a technical dashboard, based on the number of syncs.
  const maxBars = 20;
  const bars = Array.from({ length: maxBars }).map((_, i) => {
    // Fill up bars based on sync count (modulo to wrap around)
    const isFilled = i < (syncs % maxBars);
    const height = isFilled ? 40 + Math.random() * 40 : 10;
    return (
      <div 
        key={i}
        style={{
          width: '8px',
          height: `${height}%`,
          backgroundColor: isFilled ? 'var(--accent-blue)' : '#374151',
          transition: 'height 0.3s ease, background-color 0.3s ease'
        }}
      />
    );
  });

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>Federated Learning Node</span>
        <span style={{ color: 'var(--accent-blue)' }}>Syncs: {syncs}</span>
      </div>
      <div className="panel-content" style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', padding: '16px', gap: '4px' }}>
        {bars}
      </div>
    </div>
  );
}

export default FedAvgGraph;
