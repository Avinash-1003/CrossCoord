import React from 'react';

function AcademicMetrics({ metrics }) {
  if (!metrics) return null;

  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header">PhD Academic Metrics Suite</div>
      <div className="panel-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>Makespan (M)</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f3f4f6' }}>{metrics.makespan} steps</div>
        </div>
        <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>Flowtime (SOFF)</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-blue)' }}>{metrics.flowtime_soff} units</div>
        </div>
        <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>Comm Overhead</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-yellow)' }}>{metrics.comm_overhead_kb} KB</div>
        </div>
        <div style={{ backgroundColor: '#1f2937', padding: '8px', borderRadius: '4px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>Pareto Score</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-green)' }}>{metrics.pareto_efficiency}</div>
        </div>
      </div>
    </div>
  );
}

export default AcademicMetrics;
