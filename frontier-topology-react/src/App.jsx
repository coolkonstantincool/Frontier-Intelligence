import { useEffect, useState } from 'react'
import FrontierMap from './FrontierMap'

function App() {
  const [dataset, setDataset] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/dataset.json')
      .then(res => res.json())
      .then(data => {
        setDataset(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to load dataset:", err)
        setLoading(false)
      })
  }, [])

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden font-sans">
      
      {/* Premium Header */}
      <header className="flex-none px-8 py-5 flex items-center justify-between z-20 bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-sm relative">
        <div className="flex items-center gap-4">
          <div className="font-bold tracking-widest text-[16px] text-slate-900 uppercase">
            Frontier <span className="text-indigo-500">Topology</span>
          </div>
          <div className="h-4 w-px bg-slate-300"></div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-widest">
            Open Source Release
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <a href="https://github.com/coolkonstantincool/Frontier-Intelligence" target="_blank" rel="noreferrer" className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
            GitHub
          </a>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 relative flex m-2 rounded-2xl overflow-hidden border border-slate-200 shadow-inner bg-slate-50">
        
        {/* Left Sidebar (Info Panel) */}
        <aside className="absolute left-4 top-4 bottom-4 w-80 z-20 pointer-events-none">
          <div className="h-full glass-panel rounded-2xl p-6 pointer-events-auto flex flex-col gap-6">
            <div>
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-1">Dataset</h2>
              <h1 className="text-xl font-bold text-slate-900">Frontier Ecosystem</h1>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                A high-dimensional semantic mapping of the ecosystem. Projects are embedded via LLM analysis of functionality, impact, and novelty.
              </p>
            </div>
            
            <div className="bg-white/50 rounded-xl p-4 border border-white/60">
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {dataset?.points?.length || 0}
              </div>
              <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                Projects Analyzed
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              <h3 className="text-xs font-semibold text-slate-800 mb-3 uppercase tracking-wider">Semantic Clusters</h3>
              <div className="space-y-2">
                {(dataset?.hulls || []).sort((a,b)=>b.size-a.size).slice(0, 10).map(h => (
                  <div key={h.cluster_id} className="text-xs text-slate-600 flex items-center justify-between bg-white/40 px-3 py-2 rounded-lg border border-white/50">
                    <span className="truncate pr-2 font-medium">{h.label || h.top_concepts?.[0] || `Cluster ${h.cluster_id}`}</span>
                    <span className="text-indigo-500 font-semibold">{h.size}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </aside>

        {/* The Map Component */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center bg-slate-50">
            <div className="text-sm text-slate-400 uppercase tracking-widest font-medium animate-pulse">Initializing UMAP Coordinates...</div>
          </div>
        ) : (
          <FrontierMap 
            dataset={dataset}
            onProjectClick={(p) => console.log("Clicked:", p.project_name)}
          />
        )}
      </main>

    </div>
  )
}

export default App
