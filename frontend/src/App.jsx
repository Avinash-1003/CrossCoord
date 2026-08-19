import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Sky } from '@react-three/drei';
import Grid3D from './components/Grid3D';
import Agent3D from './components/Agent3D';
import HUD from './components/HUD';

function App() {
  const [globalMap, setGlobalMap] = useState([]);
  const [agents, setAgents] = useState({});
  const [events, setEvents] = useState([]);
  const [fedSyncs, setFedSyncs] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to FastAPI WebSocket
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { topic, payload } = data;
      
      setEvents(prev => [...prev.slice(-10), data]);

      if (topic === "GLOBAL_MAP_BROADCAST") {
        setGlobalMap(payload.map);
      } 
      else if (topic === "MAP_UPDATE" || topic === "PATH_BLOCKED") {
        setAgents(prev => ({
          ...prev,
          [payload.agent_id]: { 
            ...prev[payload.agent_id], 
            pos: payload.pos || prev[payload.agent_id]?.pos 
          }
        }));
      }
      else if (topic === "FED_AVG_SYNC") {
        setFedSyncs(prev => prev + 1);
      }
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const startSimulation = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send("START_SIMULATION");
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#111' }}>
      <HUD events={events} fedSyncs={fedSyncs} startSimulation={startSimulation} />
      
      <Canvas camera={{ position: [16, 20, 16], fov: 50 }}>
        <Sky sunPosition={[10, 20, 10]} />
        <ambientLight intensity={0.5} />
        <directionalLight 
          position={[10, 20, 10]} 
          intensity={1.5} 
          castShadow 
        />
        
        <Grid3D mapData={globalMap} />
        
        {Object.entries(agents).map(([id, data]) => (
          <Agent3D key={id} id={id} position={data.pos} />
        ))}
        
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}

export default App;
