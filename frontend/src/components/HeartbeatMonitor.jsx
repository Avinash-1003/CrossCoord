import React, { useEffect, useRef } from 'react';

function HeartbeatMonitor({ logs, agents }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">Heartbeat & Self-Healing Monitor</div>
      <div style={{ display: 'flex', height: '100%' }}>
        {/* Terminal Log */}
        <div className="panel-content" ref={scrollRef} style={{ flex: 2, borderRight: '1px solid var(--border-color)', backgroundColor: '#000' }}>
          {logs.length === 0 && <span style={{ color: 'var(--text-secondary)' }}>Monitoring network status...</span>}
          {logs.map((log, i) => {
            let color = 'var(--text-secondary)';
            if (log.status === "ERROR") color = 'var(--accent-red)';
            if (log.status === "RECOVER") color = 'var(--accent-yellow)';
            
            return (
              <div key={i} style={{ color, marginBottom: '4px' }}>
                <span style={{ opacity: 0.5 }}>[{new Date().toISOString().substring(11, 19)}]</span> {log.status}: {log.message}
              </div>
            );
          })}
        </div>
        
        {/* Agent Status UI */}
        <div className="panel-content" style={{ flex: 1 }}>
          {Object.entries(agents).map(([id, agent]) => {
            const isDead = logs.some(l => l.status === "ERROR" && l.message.includes(id));
            let dotColor = 'var(--accent-green)';
            if (isDead) dotColor = 'var(--accent-red)';
            
            return (
              <div key={id} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: dotColor, boxShadow: `0 0 4px ${dotColor}` }} />
                <span style={{ color: isDead ? '#ef4444' : '#f3f4f6', textDecoration: isDead ? 'line-through' : 'none' }}>
                  {id}
                </span>
                <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                  {isDead ? 'OFFLINE' : agent.status}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default HeartbeatMonitor;
