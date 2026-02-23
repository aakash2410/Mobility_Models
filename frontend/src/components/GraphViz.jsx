import React, { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function GraphViz({ isSimulated, fleetReduction, useMotorways }) {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const fgRef = useRef();

    useEffect(() => {
        // Fetch graph topography from the GNN backend
        fetch('http://localhost:8134/api/v1/data/mumbai')
            .then(res => res.json())
            .then(data => {
                if (data.nodes && data.edges) {
                    // Map nodes format
                    const mappedNodes = data.nodes.map(n => ({
                        id: n.id,
                        x: n.x, // ForceGraph will override physics, but we can set init
                        y: n.y,
                        highway: n.highway,
                        popDensity: n.population_density || 0.1,
                        wardName: n.ward_name || "Unknown Ward"
                    }));

                    // Map edges to 'links' for ForceGraph
                    const mappedLinks = data.edges.map(e => ({
                        source: e.source,
                        target: e.target,
                        highway: e.highway,
                        length: e.length,
                        name: e.name || "Unnamed Road"
                    }));

                    setGraphData({ nodes: mappedNodes, links: mappedLinks });
                }
            })
            .catch(console.error);
    }, []);

    // Zoom to fit once loaded
    useEffect(() => {
        if (graphData.nodes.length > 0 && fgRef.current) {
            // Apply a slight delay to allow physics engine to start settling
            setTimeout(() => {
                fgRef.current.zoomToFit(400, 50);
            }, 500);
        }
    }, [graphData]);

    // Graph node styling based on 'highway' classification mapping 
    const getNodeColor = (node) => {
        if (node.highway === 'primary') return '#ff3b30'; // Red for main roads
        if (node.highway === 'secondary') return '#ff9500'; // Orange
        return '#4cd964'; // Green for residential/micromobility
    }

    const getLinkColor = (link) => {
        if (link.highway === 'primary') return 'rgba(255, 59, 48, 0.4)';
        if (link.highway === 'secondary') return 'rgba(255, 149, 0, 0.3)';
        return 'rgba(76, 217, 100, 0.2)';
    }

    // Dynamic Visualizations based on GNN Simulation State
    const getParticleCount = (link) => {
        if (!isSimulated) return 0;

        // High reduction (MaaS) -> efficient routing, fewer dense particles
        // Low reduction (POV) -> massive congestion, lots of particles
        const isMaaS = fleetReduction > 50;

        if (isMaaS) {
            // MaaS prioritizes motorways
            return link.highway === 'primary' && useMotorways ? 2 : 1;
        } else {
            // Chaotic POV traffic everywhere
            return link.highway === 'primary' ? 6 : 4;
        }
    };

    const getParticleSpeed = (link) => {
        if (!isSimulated) return 0;

        const isMaaS = fleetReduction > 50;
        if (isMaaS) {
            // Smooth fast flow
            return link.highway === 'primary' && useMotorways ? 0.04 : 0.02;
        } else {
            // Gridlock congestion speeds
            return 0.005;
        }
    };

    const getParticleColor = (link) => {
        const isMaaS = fleetReduction > 50;
        return isMaaS ? '#00f0ff' : '#ff3b30'; // Neon Cyan for MaaS, Red for Traffic
    };

    if (graphData.nodes.length === 0) {
        return (
            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0B0E14', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ textAlign: 'center' }}>
                    <h3 style={{ color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>Graph Visualization Render Area</h3>
                    <p className="loading-pulse" style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.9rem' }}>Fetching Mumbai Topography from PyTorch Backend...</p>
                </div>
            </div>
        )
    }

    return (
        <div style={{ width: '100%', height: '100%', borderRadius: '16px', overflow: 'hidden', backgroundColor: '#020305' }}>
            <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeAutoColorBy="group"
                nodeVal={node => (node.popDensity * 5) + 1} // Scale node size by our true Mumbai real-world population density
                nodeColor={getNodeColor}
                nodeLabel={node => `<div style="background: rgba(0,0,0,0.8); padding: 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2);"><strong style="color: #fff;">${node.wardName}</strong><br/><span style="color: rgba(255,255,255,0.7)">Density: ${(node.popDensity * 114000).toLocaleString()} / sq km</span></div>`}
                linkColor={getLinkColor}
                linkLabel={link => `<div style="background: rgba(0,0,0,0.8); padding: 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); color: #fff;">${link.name} <span style="color: rgba(255,255,255,0.5); font-size: 0.8em;">(${link.highway})</span></div>`}
                linkWidth={link => link.highway === 'primary' ? 2 : 0.8}
                linkDirectionalParticles={getParticleCount}
                linkDirectionalParticleSpeed={getParticleSpeed}
                linkDirectionalParticleColor={getParticleColor}
                linkDirectionalParticleWidth={2}
                d3VelocityDecay={0.9} // Increase decay to stop endless jittering faster
            />
        </div>
    )
}
