import React, { useState, useEffect, useRef } from 'react';
import TacticalRadar from './components/TacticalRadar';
import LLMCortex from './components/LLMCortex';
import DQNTelemetry from './components/DQNTelemetry';
import FedAvgGraph from './components/FedAvgGraph';
import HeartbeatMonitor from './components/HeartbeatMonitor';
import C2ControlPanel from './components/C2ControlPanel';
import CBSVisualizer from './components/CBSVisualizer';
import MeshTopology from './components/MeshTopology';
import AcademicMetrics from './components/AcademicMetrics';

function App() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [domain, setDomain] = useState("disaster_relief");
  
  // State from backend
  const [globalMap, setGlobalMap] = useState([]);
  const [agents, setAgents] = useState({});
  const [llmLogs, setLlmLogs] = useState([]);
  const [dqnStats, setDqnStats] = useState({});
  const [heartbeatLogs, setHeartbeatLogs] = useState([]);
  const [fedSyncs, setFedSyncs] = useState(0);
  const [summaryResult, setSummaryResult] = useState(null);
  
  // PhD Level State
  const [cbsData, setCbsData] = useState(null);
  const [meshData, setMeshData] = useState(null);
  const [academicMetrics, setAcademicMetrics] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    
    ws.onopen = () => {
      setConnected(true);
      setSocket(ws);
      // Auto-deploy simulation immediately on connection open
      ws.send(JSON.stringify({ cmd: "START_SIMULATION", domain: "disaster_relief" }));
    };
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const { topic, payload } = msg;
      
      if (topic === "GLOBAL_MAP_BROADCAST") {
        setGlobalMap(payload.map);
      } 
      else if (topic === "MAP_UPDATE" || topic === "PATH_BLOCKED" || topic === "AGENT_MOVED") {
        setAgents(prev => ({
          ...prev,
          [payload.agent_id]: { 
            pos: payload.pos, 
            status: topic === "PATH_BLOCKED" ? "BLOCKED" : "ACTIVE"
          }
        }));
      }
      else if (topic === "FED_AVG_SYNC") {
        setFedSyncs(prev => prev + 1);
      }
      else if (topic === "LLM_REASONING") {
        setLlmLogs(prev => [...prev, payload]);
      }
      else if (topic === "DQN_TELEMETRY") {
        setDqnStats(prev => ({
          ...prev,
          [payload.agent_id]: payload
        }));
      }
      else if (topic === "HEARTBEAT") {
        setHeartbeatLogs(prev => [...prev, payload]);
      }
      else if (topic === "CBS_TELEMETRY") {
        setCbsData(payload);
      }
      else if (topic === "MESH_TELEMETRY") {
        setMeshData(payload);
      }
      else if (topic === "ACADEMIC_METRICS") {
        setAcademicMetrics(payload);
      }
      else if (topic === "SIMULATION_COMPLETE") {
        setSummaryResult(payload);
      }
      else if (topic === "TASK_COMPLETED") {
        setAgents(prev => ({
          ...prev,
          [payload.agent_id]: {
            ...prev[payload.agent_id],
            status: "COMPLETED"
          }
        }));
      }
    };
    
    ws.onclose = () => setConnected(false);
    return () => ws.close();
  }, []);

  const handleDeploy = () => {
    if (socket && connected) {
      setGlobalMap([]);
      setAgents({});
      setLlmLogs([]);
      setDqnStats({});
      setHeartbeatLogs([]);
      setFedSyncs(0);
      setSummaryResult(null);
      setCbsData(null);
      setMeshData(null);
      setAcademicMetrics(null);
      
      socket.send(JSON.stringify({ cmd: "START_SIMULATION", domain }));
    }
  };

  const handleInjectFailure = (agent_id) => {
    if (socket && connected) {
      socket.send(JSON.stringify({ cmd: "INJECT_FAILURE", agent_id }));
    }
  };

  const handleTriggerFL = () => {
    if (socket && connected) {
      socket.send(JSON.stringify({ cmd: "TRIGGER_FL" }));
    }
  };

  return (
    <div className="dashboard-container" style={{ position: 'relative' }}>
      {/* Evaluation Results Modal */}
      {summaryResult && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.85)',
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <div style={{
            backgroundColor: '#111827',
            border: '2px solid var(--accent-blue)',
            borderRadius: '12px',
            padding: '32px',
            width: '450px',
            boxShadow: '0 0 30px rgba(59, 130, 246, 0.4)',
            textAlign: 'center'
          }}>
            <h2 style={{ margin: '0 0 8px 0', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-primary)' }}>
              Mission Evaluation Complete
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--accent-green)', fontWeight: 'bold', marginBottom: '24px' }}>
              ● {summaryResult.status}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', textAlign: 'left', marginBottom: '24px' }}>
              <div style={{ backgroundColor: '#1f2937', padding: '12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Steps</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#f3f4f6' }}>{summaryResult.total_steps}</div>
              </div>
              <div style={{ backgroundColor: '#1f2937', padding: '12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Map Discovery Rate</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--accent-blue)' }}>{summaryResult.map_discovery_rate}%</div>
              </div>
              <div style={{ backgroundColor: '#1f2937', padding: '12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>FedAvg Model Syncs</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--accent-green)' }}>{summaryResult.fed_syncs}</div>
              </div>
              <div style={{ backgroundColor: '#1f2937', padding: '12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Self-Healing Events</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--accent-yellow)' }}>{summaryResult.self_healing_count}</div>
              </div>
            </div>

            <button 
              className="btn-deploy" 
              style={{ width: '100%', padding: '12px' }}
              onClick={() => setSummaryResult(null)}
            >
              Dismiss Evaluation Report
            </button>
          </div>
        </div>
      )}

      <div className="header">
        <h1>CrossCoord <span>C2 Terminal</span></h1>
        <C2ControlPanel 
          domain={domain}
          setDomain={setDomain}
          onDeploy={handleDeploy}
          onInjectFailure={handleInjectFailure}
          onTriggerFL={handleTriggerFL}
          connected={connected}
        />
      </div>

      {/* Left Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <LLMCortex logs={llmLogs} />
        <CBSVisualizer cbsData={cbsData} />
      </div>

      {/* Center Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <TacticalRadar mapData={globalMap} agents={agents} />
        <AcademicMetrics metrics={academicMetrics} />
      </div>

      {/* Right Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <DQNTelemetry stats={dqnStats} />
        <MeshTopology meshData={meshData} />
      </div>

      {/* Bottom Row */}
      <div style={{ gridColumn: '1 / 2' }}>
        <FedAvgGraph syncs={fedSyncs} />
      </div>
      <div style={{ gridColumn: '2 / 4' }}>
        <HeartbeatMonitor logs={heartbeatLogs} agents={agents} />
      </div>
    </div>
  );
}

export default App;
