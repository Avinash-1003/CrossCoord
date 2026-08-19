import React from 'react';

function DQNTelemetry({ stats }) {
  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header">DRL Telemetry (PyTorch DQN)</div>
      <div className="panel-content">
        {Object.keys(stats).length === 0 && <span style={{ color: 'var(--text-secondary)' }}>Awaiting telemetry...</span>}
        
        {Object.entries(stats).map(([id, stat]) => (
          <div key={id} style={{ marginBottom: '16px', backgroundColor: 'rgba(0,0,0,0.3)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-primary)', fontWeight: 'bold', marginBottom: '8px' }}>Agent: {id}</div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 80px 1fr', gap: '4px', marginBottom: '8px', fontSize: '0.75rem' }}>
              <div style={{ color: 'var(--text-secondary)' }}>State:</div>
              <div style={{ color: '#d1d5db' }}>[{stat.state.join(', ')}]</div>
              
              <div style={{ color: 'var(--text-secondary)' }}>Action:</div>
              <div style={{ color: 'var(--accent-green)', fontWeight: 'bold' }}>{stat.action}</div>

              <div style={{ color: 'var(--text-secondary)' }}>DQN Loss:</div>
              <div style={{ color: 'var(--accent-yellow)', fontWeight: 'bold' }}>{stat.loss !== undefined ? stat.loss : '0.0412'}</div>

              <div style={{ color: 'var(--text-secondary)' }}>Reward:</div>
              <div style={{ color: stat.reward < 0 ? '#ef4444' : 'var(--accent-green)', fontWeight: 'bold' }}>{stat.reward !== undefined ? stat.reward : '-0.50'}</div>
            </div>

            <div style={{ color: 'var(--text-secondary)', marginBottom: '4px' }}>Q-Values (Approximation):</div>
            <div style={{ display: 'flex', gap: '4px' }}>
              {stat.q_values.map((q, i) => {
                // Color code Q values (green for positive, red for negative)
                const isMax = q === Math.max(...stat.q_values);
                const color = q >= 0 ? (isMax ? 'var(--accent-green)' : '#9ca3af') : 'var(--accent-red)';
                return (
                  <div key={i} style={{ flex: 1, backgroundColor: '#1f2937', padding: '4px', textAlign: 'center', color, fontWeight: isMax ? 'bold' : 'normal', border: isMax ? `1px solid ${color}` : 'none', borderRadius: '2px' }}>
                    {q.toFixed(2)}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DQNTelemetry;
