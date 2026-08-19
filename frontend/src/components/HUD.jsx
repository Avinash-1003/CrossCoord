import React from 'react';
import { Activity, Radio, Cpu, Navigation, AlertTriangle } from 'lucide-react';

export default function HUD({ events, fedSyncs, startSimulation }) {
  return (
    <div style={{
      position: 'absolute',
      top: 0, left: 0,
      width: '100%', height: '100%',
      pointerEvents: 'none',
      zIndex: 10
    }}>
      {/* Top Bar */}
      <div style={{
        padding: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        background: 'linear-gradient(180deg, rgba(0,0,0,0.8) 0%, transparent 100%)'
      }}>
        <div style={{ color: 'white', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu color="#3b82f6" />
          <h1 style={{ margin: 0, fontSize: '24px', letterSpacing: '2px' }}>CROSSCOORD <span style={{fontWeight: 300}}>DIGITAL TWIN</span></h1>
        </div>
        
        <div style={{ display: 'flex', gap: '20px' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '10px 20px', borderRadius: '8px', border: '1px solid #3b82f6', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#60a5fa" />
            <span>FedAvg Syncs: <strong>{fedSyncs}</strong></span>
          </div>
          <button 
            onClick={startSimulation}
            style={{
              pointerEvents: 'auto',
              background: '#22c55e',
              color: 'black',
              border: 'none',
              padding: '10px 24px',
              borderRadius: '8px',
              fontWeight: 'bold',
              cursor: 'pointer',
              boxShadow: '0 0 15px rgba(34, 197, 94, 0.5)'
            }}>
            DEPLOY MISSION
          </button>
        </div>
      </div>

      {/* Mission Log (Bottom Left) */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        width: '400px',
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '12px',
        padding: '15px',
        color: 'white',
        maxHeight: '300px',
        overflow: 'hidden'
      }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#9ca3af', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={14} /> LIVE EVENT STREAM
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {events.map((ev, i) => (
            <div key={i} style={{ 
              fontSize: '13px', 
              fontFamily: 'monospace',
              padding: '8px',
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '6px',
              borderLeft: ev.topic === 'PATH_BLOCKED' ? '3px solid #ef4444' : '3px solid #3b82f6'
            }}>
              <strong style={{ color: ev.topic === 'PATH_BLOCKED' ? '#fca5a5' : '#93c5fd' }}>[{ev.topic}]</strong> 
              <br/>
              <span style={{ color: '#d1d5db' }}>{JSON.stringify(ev.payload)}</span>
            </div>
          ))}
          {events.length === 0 && <div style={{ color: '#6b7280', fontStyle: 'italic' }}>Waiting for telemetry...</div>}
        </div>
      </div>
    </div>
  );
}
