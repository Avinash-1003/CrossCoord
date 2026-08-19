import React, { useEffect, useRef } from 'react';

function LLMCortex({ logs }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header">LLM & RAG Cortex</div>
      <div className="panel-content" ref={scrollRef}>
        {logs.length === 0 && <span style={{ color: 'var(--text-secondary)' }}>Awaiting telemetry...</span>}
        
        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: '16px', borderLeft: '2px solid var(--accent-blue)', paddingLeft: '8px' }}>
            <div style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>[{log.tier}] {log.action}</div>
            <div style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Input:</div>
            <pre style={{ margin: '4px 0', whiteSpace: 'pre-wrap', color: '#e5e7eb' }}>
              {typeof log.input === 'object' ? JSON.stringify(log.input, null, 2) : log.input}
            </pre>
            <div style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Output:</div>
            <pre style={{ margin: '4px 0', whiteSpace: 'pre-wrap', color: 'var(--accent-green)' }}>
              {JSON.stringify(log.output, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LLMCortex;
