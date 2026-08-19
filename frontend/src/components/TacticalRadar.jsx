import React from 'react';

function TacticalRadar({ mapData, agents }) {
  const h = mapData.length || 32;
  const w = mapData[0]?.length || 32;

  // Calculate cell size to fit the container roughly
  const cellSize = 12;

  return (
    <div className="panel" style={{ flexGrow: 1 }}>
      <div className="panel-header">Tactical Radar [Sector 4]</div>
      <div className="panel-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#000' }}>
        
        <div 
          style={{ 
            display: 'grid', 
            gridTemplateColumns: `repeat(${w}, ${cellSize}px)`,
            gridTemplateRows: `repeat(${h}, ${cellSize}px)`,
            border: '1px solid #374151',
            position: 'relative'
          }}
        >
          {mapData.length > 0 && mapData.map((row, r) => 
            row.map((val, c) => {
              let bg = '#111827'; // Unknown (-1)
              let animation = 'none';
              if (val === 0) bg = '#064e3b'; // Passable (Dark Green)
              if (val === 1) bg = '#7f1d1d'; // Obstacle (Dark Red)
              if (val === 2) {
                bg = '#c2410c'; // Dynamic Hazard (Expanding Fire/Gas - Orange/Red)
                animation = 'pulse 1.5s infinite alternate';
              }
              
              return (
                <div 
                  key={`${r}-${c}`}
                  style={{
                    width: cellSize,
                    height: cellSize,
                    backgroundColor: bg,
                    borderRight: '1px solid #1f2937',
                    borderBottom: '1px solid #1f2937',
                    animation
                  }}
                />
              );
            })
          )}

          {/* Render Agents */}
          {Object.entries(agents).map(([id, agent]) => {
            if (!agent.pos) return null;
            const [r, c] = agent.pos;
            const isCompleted = agent.status === "COMPLETED";
            const isBlocked = agent.status === "BLOCKED";
            
            let color = 'var(--accent-blue)';
            if (isCompleted) color = 'var(--accent-green)';
            if (isBlocked) color = 'var(--accent-yellow)';
            if (id === "A_006") color = 'var(--accent-yellow)'; // just to differentiate
            
            return (
              <div 
                key={id}
                style={{
                  position: 'absolute',
                  top: r * cellSize,
                  left: c * cellSize,
                  width: cellSize,
                  height: cellSize,
                  backgroundColor: color,
                  boxShadow: `0 0 8px ${color}`,
                  borderRadius: '50%',
                  transform: 'scale(1.2)',
                  transition: 'all 0.2s ease',
                  zIndex: 10
                }}
              >
                <div style={{ position: 'absolute', top: -15, left: -10, color: 'white', fontSize: '9px', fontWeight: 'bold' }}>
                  {id}
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}

export default TacticalRadar;
