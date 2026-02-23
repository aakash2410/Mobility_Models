import React, { useState } from 'react';
import GraphViz from './GraphViz';

export default function Dashboard() {
    const [fleetReduction, setFleetReduction] = useState(90);
    const [useMotorways, setUseMotorways] = useState(true);

    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [isSimulated, setIsSimulated] = useState(false);

    const startSimulation = async () => {
        setLoading(true);
        try {
            const config = {
                fleet_reduction_percentage: fleetReduction,
                use_motorways: useMotorways,
                maas_tier_distribution: { platinum: 10, gold: 20, silver: 40, economy: 30 },
                eliminate_parking: true
            };

            const response = await fetch('http://localhost:8134/api/v1/simulate/ultra', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            const data = await response.json();
            setMetrics(data);
            setIsSimulated(true);
        } catch (error) {
            console.error("Simulation failed:", error);
            alert("Failed to reach GNN backend.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: '350px 1fr',
            gap: '24px',
            height: 'calc(100vh - 140px)', // account for header
        }}>
            {/* Control Panel */}
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                    <h2 style={{ marginBottom: '4px', fontSize: '1.4rem' }}>Parameters</h2>
                    <p className="subtitle" style={{ fontSize: '0.9rem' }}>Configure ULTRA Hypotheses</p>
                </div>

                <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)' }} />

                <div>
                    <label>Target Fleet Reduction (PVO Abolition)</label>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--color-primary)' }}>
                        <span>0%</span>
                        <span style={{ fontWeight: 'bold' }}>{fleetReduction}%</span>
                        <span>100%</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={fleetReduction}
                        onChange={(e) => setFleetReduction(e.target.value)}
                    />
                </div>

                <div>
                    <label>Functional Separation (Motorways)</label>
                    <label className="toggle-switch">
                        <input type="checkbox" checked={useMotorways} onChange={() => setUseMotorways(!useMotorways)} />
                        <span className="toggle-slider"></span>
                        <span style={{ color: '#fff', fontSize: '0.95rem' }}>Enable Dedicated Motorways</span>
                    </label>
                </div>

                <div style={{ flexGrow: 1 }}></div>

                <button className="btn-primary" onClick={startSimulation} disabled={loading}>
                    {loading ? 'Running GNN...' : 'Run GNN Simulation'}
                </button>

                {metrics && (
                    <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                        <h3 style={{ fontSize: '1rem', marginBottom: '16px', color: 'var(--color-primary)' }}>{metrics.scenario}</h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ color: 'rgba(255,255,255,0.6)' }}>Traffic Density:</span>
                                <strong>{metrics.conflict_density}%</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ color: 'rgba(255,255,255,0.6)' }}>Avg Travel Time:</span>
                                <strong>{metrics.avg_travel_time_mins} mins</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ color: 'rgba(255,255,255,0.6)' }}>Fleet Utilization:</span>
                                <strong>{metrics.fleet_utilization_pct}%</strong>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Main Graph Area */}
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
                <GraphViz
                    isSimulated={isSimulated}
                    fleetReduction={fleetReduction}
                    useMotorways={useMotorways}
                />
            </div>
        </div>
    )
}
