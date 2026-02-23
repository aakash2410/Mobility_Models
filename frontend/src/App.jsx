import React from 'react'
import Dashboard from './components/Dashboard'

function App() {
    return (
        <div style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto' }}>
            <header style={{ marginBottom: '32px' }}>
                <h1>MaaS Movement</h1>
                <p className="subtitle">ULTRA Bill Mobility Hypothesis Engine &bull; Mumbai Simulation Network</p>
            </header>

            <main>
                <Dashboard />
            </main>
        </div>
    )
}

export default App
