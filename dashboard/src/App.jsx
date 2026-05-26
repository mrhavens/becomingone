import React, { useState, useEffect, useRef } from 'react';
import { Activity, Clock, Zap, Network, Brain } from 'lucide-react';
import './index.css';

const NUM_OSCILLATORS = 8;
const RADIUS = 100;

function App() {
  const [coherence, setCoherence] = useState(0.85);
  const [entropy, setEntropy] = useState(1.2);
  const [tokenFreq, setTokenFreq] = useState(15.4);
  const [phases, setPhases] = useState(Array(NUM_OSCILLATORS).fill(0).map((_, i) => (i * 2 * Math.PI) / NUM_OSCILLATORS));
  const [logs, setLogs] = useState([
    { time: new Date().toLocaleTimeString(), msg: "KAIROS Temporal Engine Initialized." },
    { time: new Date().toLocaleTimeString(), msg: "Kuramoto coupling established at K=2.4" }
  ]);
  
  const frameRef = useRef(null);

  // Simulate Kuramoto Phase Dynamics
  useEffect(() => {
    let lastTime = performance.now();
    
    const animate = (time) => {
      const dt = (time - lastTime) / 1000;
      lastTime = time;
      
      setPhases(prev => {
        const newPhases = [...prev];
        const K = 2.5; // Coupling constant
        const N = NUM_OSCILLATORS;
        const omega = 1.0; // Natural frequency
        
        for (let i = 0; i < N; i++) {
          let sum = 0;
          for (let j = 0; j < N; j++) {
            sum += Math.sin(prev[j] - prev[i]);
          }
          // Add some stochastic resonance (noise)
          const noise = (Math.random() - 0.5) * 0.2;
          newPhases[i] += (omega + (K / N) * sum + noise) * dt;
        }
        return newPhases;
      });

      // Fluctuate metrics slightly
      if (Math.random() > 0.95) {
        setTokenFreq(prev => +(prev + (Math.random() - 0.5)).toFixed(1));
        setCoherence(prev => Math.min(1, Math.max(0, prev + (Math.random() - 0.5) * 0.05)));
        setEntropy(prev => Math.max(0, prev + (Math.random() - 0.5) * 0.1));
      }

      frameRef.current = requestAnimationFrame(animate);
    };
    
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  // Add random logs to simulate engine activity
  useEffect(() => {
    const interval = setInterval(() => {
      setLogs(prev => {
        const newLogs = [...prev, {
          time: new Date().toLocaleTimeString(),
          msg: `Phase integrated. Coherence: ${(coherence * 100).toFixed(1)}%. Vector hash committed to Ledger.`
        }];
        return newLogs.slice(-10); // Keep last 10
      });
    }, 4000);
    return () => clearInterval(interval);
  }, [coherence]);

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1 className="title">BecomingONE // Temporal Dashboard</h1>
        <div className="status-badge">
          <div className="pulse"></div>
          PHASE LOCKED
        </div>
      </header>

      <div className="grid">
        {/* Visualizer Card */}
        <div className="card col-span-8">
          <div className="card-header">
            <h2 className="card-title">Kuramoto Oscillator Manifold</h2>
            <Network size={20} color="var(--text-secondary)" />
          </div>
          <div className="phase-visualizer">
            <div className="oscillator-circle"></div>
            {phases.map((phase, i) => {
              const x = Math.cos(phase) * RADIUS;
              const y = Math.sin(phase) * RADIUS;
              const isLeader = i === 0;
              return (
                <div 
                  key={i} 
                  className={`oscillator-node ${isLeader ? 'leader' : ''}`}
                  style={{
                    transform: `translate(${x}px, ${y}px)`
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Metrics Column */}
        <div className="card col-span-4">
          <div className="card-header">
            <h2 className="card-title">System Metrics</h2>
            <Activity size={20} color="var(--text-secondary)" />
          </div>
          
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              <Zap size={16} /> Global Coherence
            </div>
            <div className="metric-value">
              {(coherence * 100).toFixed(1)}<span className="metric-unit">%</span>
            </div>
            <div className="chart-bar-container">
              <div className="chart-bar-fill" style={{ width: `${coherence * 100}%` }}></div>
            </div>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              <Clock size={16} /> Token Clock (dt)
            </div>
            <div className="metric-value">
              {tokenFreq.toFixed(1)}<span className="metric-unit">Hz</span>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              <Brain size={16} /> Attention Entropy
            </div>
            <div className="metric-value">
              {entropy.toFixed(2)}<span className="metric-unit">nats</span>
            </div>
          </div>
        </div>

        {/* Temporal Ledger Logs */}
        <div className="card col-span-12">
          <div className="card-header">
            <h2 className="card-title">Merkle Ledger Stream</h2>
          </div>
          <div className="log-container">
            {logs.map((log, i) => (
              <div key={i} className="log-entry">
                <span className="log-time">[{log.time}]</span>
                {log.msg}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
