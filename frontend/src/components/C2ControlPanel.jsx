import React from 'react';

function C2ControlPanel({ domain, setDomain, onDeploy, onInjectFailure, onTriggerFL, connected }) {
  return (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'center', backgroundColor: '#111827', padding: '8px 16px', borderRadius: '8px', border: '1px solid #1f2937' }}>
      
      {/* Domain Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Domain:</span>
        <select 
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          style={{
            backgroundColor: '#1f2937',
            color: '#f3f4f6',
            border: '1px solid #374151',
            borderRadius: '4px',
            padding: '4px 8px',
            fontSize: '0.8rem'
          }}
        >
          <option value="disaster_relief">Disaster Relief</option>
          <option value="logistics">Warehouse Logistics</option>
          <option value="search_and_rescue">Urban Search & Rescue</option>
        </select>
      </div>

      {/* Inject Fault Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--accent-red)', textTransform: 'uppercase', fontWeight: 'bold' }}>Inject Fault:</span>
        {['A_003', 'A_004', 'A_005', 'A_006'].map(aid => (
          <button
            key={aid}
            onClick={() => onInjectFailure(aid)}
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              color: 'var(--accent-red)',
              border: '1px solid var(--accent-red)',
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '0.7rem',
              cursor: 'pointer'
            }}
          >
            Kill {aid}
          </button>
        ))}
      </div>

      {/* Manual FL Trigger */}
      <button
        onClick={onTriggerFL}
        style={{
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          color: 'var(--accent-green)',
          border: '1px solid var(--accent-green)',
          borderRadius: '4px',
          padding: '4px 8px',
          fontSize: '0.75rem',
          cursor: 'pointer',
          fontWeight: 'bold'
        }}
      >
        Force FL Sync
      </button>

      {/* Export IEEE Paper Button */}
      <button
        onClick={() => window.open('http://localhost:8000/export_paper', '_blank')}
        style={{
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          color: 'var(--accent-blue)',
          border: '1px solid var(--accent-blue)',
          borderRadius: '4px',
          padding: '4px 8px',
          fontSize: '0.75rem',
          cursor: 'pointer',
          fontWeight: 'bold'
        }}
      >
        📄 Export IEEE Paper
      </button>

      {/* Deploy Button */}
      <button className="btn-deploy" onClick={onDeploy} disabled={!connected}>
        Deploy Mission
      </button>
    </div>
  );
}

export default C2ControlPanel;
