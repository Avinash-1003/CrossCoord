import React from 'react';

function MeshTopology({ meshData }) {
  if (!meshData || !meshData.adjacency_matrix) {
    return (
      <div className="panel" style={{ flexGrow: 1 }}>
        <div className="panel-header">Ad-Hoc RF Mesh Topology (A_ij Matrix)</div>
        <div className="panel-content">
          <span style={{ color: 'var(--text-secondary)' }}>Awaiting RF network simulation...</span>
        </div>
      </div>
    );
  }

  const agents = meshData.agents || [];
  const matrix = meshData.adjacency_matrix || [];

  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>Ad-Hoc RF Mesh Topology (A_ij Matrix)</span>
        <span style={{ color: 'var(--accent-blue)' }}>Links: {meshData.mesh_active_links}</span>
      </div>
      <div className="panel-content" style={{ padding: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: `40px repeat(${agents.length}, 1fr)`, gap: '2px', textAlign: 'center', fontSize: '0.7rem' }}>
          <div></div>
          {agents.map(aid => (
            <div key={aid} style={{ color: 'var(--text-secondary)', fontWeight: 'bold' }}>{aid.split('_')[1]}</div>
          ))}
          
          {matrix.map((row, i) => (
            <React.Fragment key={i}>
              <div style={{ color: 'var(--text-secondary)', fontWeight: 'bold', alignSelf: 'center' }}>{agents[i]?.split('_')[1]}</div>
              {row.map((val, j) => {
                const isSelf = i === j;
                const isConnected = val > 0;
                let bg = isSelf ? '#374151' : isConnected ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.15)';
                let color = isSelf ? '#9ca3af' : isConnected ? 'var(--accent-green)' : 'var(--accent-red)';
                
                return (
                  <div key={j} style={{ backgroundColor: bg, color, padding: '4px 0', borderRadius: '2px', fontWeight: 'bold' }}>
                    {isConnected ? '1' : '0'}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MeshTopology;
