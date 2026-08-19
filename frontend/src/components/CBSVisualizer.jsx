import React from 'react';

function CBSVisualizer({ cbsData }) {
  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>CBS Solver (Conflict-Based MAPF)</span>
        <span style={{ color: 'var(--accent-green)' }}>{cbsData?.status || 'AWAITING_CBS'}</span>
      </div>
      <div className="panel-content">
        {!cbsData ? (
          <span style={{ color: 'var(--text-secondary)' }}>Awaiting MAPF constraint tree search...</span>
        ) : (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>CT Nodes Expanded</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-blue)' }}>{cbsData.nodes_expanded}</div>
              </div>
              <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>Conflicts Resolved</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-yellow)' }}>{cbsData.conflicts_resolved}</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span>Solver Execution Time:</span>
              <span style={{ color: '#f3f4f6', fontWeight: 'bold' }}>{cbsData.solve_time_ms} ms</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CBSVisualizer;
