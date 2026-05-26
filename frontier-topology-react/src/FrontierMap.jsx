import React, { useEffect, useRef, useState, useCallback } from 'react'
import Graph from 'graphology'
import Sigma from 'sigma'
import { createNodeImageProgram } from '@sigma/node-image'

const ARCHETYPE_PALETTE = [
  '#4F6BF6', '#06B6D4', '#10B981', '#8B5CF6', '#F59E0B',
  '#EC4899', '#EF4444', '#14B8A6', '#F97316', '#6366F1',
]

function getArchetypeColor(arch, index) {
  if (!arch) return '#B0B0B0'
  return ARCHETYPE_PALETTE[index % ARCHETYPE_PALETTE.length]
}

export default function FrontierMap({ dataset, onProjectClick, onProjectHover }) {
  const containerRef = useRef(null)
  const sigmaRef = useRef(null)
  const graphRef = useRef(null)
  const labelsRef = useRef({})
  
  const [hoverNode, setHoverNode] = useState(null)
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 })

  // Calculate distinct archetypes to map colors consistently
  const archetypeMap = useRef(new Map())

  const updateLabels = useCallback(() => {
    if (!sigmaRef.current || !dataset?.hulls) return
    const cam = sigmaRef.current.getCamera()
    const ratio = cam.ratio
    
    const sortedHulls = [...dataset.hulls].sort((a, b) => b.size - a.size)
    const boxes = []
    
    sortedHulls.forEach(h => {
      const el = labelsRef.current[h.cluster_id]
      const bgEl = document.getElementById(`semantic-region-${h.cluster_id}`)
      
      if (el || bgEl) {
        const vp = sigmaRef.current.graphToViewport({ x: h.centroid[0], y: h.centroid[1] })
        
        if (bgEl) {
           const bgScale = Math.min(6, Math.max(1, 1 / ratio))
           bgEl.style.transform = `translate3d(${vp.x}px, ${vp.y}px, 0) translate(-50%, -50%) scale(${bgScale})`
        }

        if (el) {
          let opacity = 1;
          if (ratio < 0.1) opacity = 0 
          else if (ratio > 3.0) opacity = Math.max(0, 1 - (ratio - 3.0) / 1.5)
          
          if (boxes.length >= 15) opacity = 0;
          
          const scaleFactor = Math.min(1.5, Math.max(0.85, 1 / Math.pow(ratio, 0.3)))
          let collision = false
          
          if (opacity > 0) {
             const width = 180 * scaleFactor 
             const height = 30 * scaleFactor
             const padding = 20
             const box = { l: vp.x - width/2 - padding, r: vp.x + width/2 + padding, t: vp.y - height/2 - padding, b: vp.y + height/2 + padding }
             
             for (let b of boxes) {
                if (!(box.l > b.r || box.r < b.l || box.t > b.b || box.b < b.t)) {
                    collision = true; break
                }
             }
             if (!collision) boxes.push(box)
          }
          
          if (collision) opacity = 0
          
          el.style.transform = `translate3d(${vp.x}px, ${vp.y}px, 0) translate(-50%, -50%) scale(${scaleFactor})`
          el.style.opacity = opacity
          el.style.pointerEvents = opacity > 0 ? 'auto' : 'none'
        }
      }
    })
  }, [dataset])

  useEffect(() => {
    if (!dataset?.points || !containerRef.current) return
    if (sigmaRef.current) { sigmaRef.current.kill(); sigmaRef.current = null }

    const graph = new Graph()
    graphRef.current = graph

    // Map archetypes to consistent indices
    dataset.points.forEach(p => {
      if (p.archetype && !archetypeMap.current.has(p.archetype)) {
        archetypeMap.current.set(p.archetype, archetypeMap.current.size)
      }
    })

    const clusterNodes = {}
    dataset.points.forEach(p => {
      const c = p.cluster ?? -1
      if (!clusterNodes[c]) clusterNodes[c] = []
      clusterNodes[c].push(p)
    })
    const clusterHeroes = new Set()
    Object.values(clusterNodes).forEach(nodes => {
      nodes.sort((a, b) => (b.size || 0) - (a.size || 0))
      nodes.slice(0, 3).forEach(n => clusterHeroes.add(n.project_id))
    })

    dataset.points.forEach(p => {
      p.is_hero = clusterHeroes.has(p.project_id)
      const colorIndex = archetypeMap.current.get(p.archetype) || 0
      
      graph.addNode(p.project_id, {
        x: p.x, 
        y: p.y,
        size: p.is_hero ? 4 : 2,
        color: getArchetypeColor(p.archetype, colorIndex),
        label: p.project_name,
        type: 'circle',
        _data: p,
      })
    })

    if (dataset.edges) {
      dataset.edges.forEach((edge, i) => {
        if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
          if (!graph.hasEdge(edge.source, edge.target)) {
             graph.addEdge(edge.source, edge.target, {
               size: edge.weight * 2 || 1,
               color: 'rgba(226, 232, 240, 0.4)'
             })
          }
        }
      })
    }

    const sigma = new Sigma(graph, containerRef.current, {
      defaultNodeType: 'circle',
      nodeProgramClasses: { image: createNodeImageProgram({ correctCentering: true }) },
      renderLabels: true,
      labelRenderedSizeThreshold: 14,
      labelDensity: 0.05,
      labelSize: 11,
      labelWeight: '600',
      labelFont: 'Inter',
      labelColor: { color: '#0F172A' },
      defaultNodeColor: '#D4D4D4',
      stagePadding: 60,
      minCameraRatio: 0.015,
      maxCameraRatio: 5,
      allowInvalidContainer: true,
    })

    sigma.on('afterRender', updateLabels)
    sigma.getCamera().on('updated', () => sigma.refresh())

    if (onProjectClick) {
      sigma.on('clickNode', ({ node }) => onProjectClick(graph.getNodeAttributes(node)._data))
    }

    let hoverTimeout = null
    sigma.on('enterNode', ({ node }) => {
      if (hoverTimeout) clearTimeout(hoverTimeout)
      hoverTimeout = setTimeout(() => {
        const nd = graph.getNodeAttributes(node)
        const pos = sigma.graphToViewport({ x: nd.x, y: nd.y })
        setHoverNode(nd._data)
        setHoverPos({ x: pos.x, y: pos.y })
        if (onProjectHover) onProjectHover(nd._data)
      }, 100)
    })
    sigma.on('leaveNode', () => {
      if (hoverTimeout) clearTimeout(hoverTimeout)
      setHoverNode(null)
      if (onProjectHover) onProjectHover(null)
    })

    sigmaRef.current = sigma
    updateLabels()

    return () => {
      sigma.kill()
      graph.clear()
    }
  }, [dataset, onProjectClick, onProjectHover, updateLabels])

  return (
    <div className="w-full h-full relative overflow-hidden bg-slate-50">
      
      {/* Semantic Region Backgrounds */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        {dataset?.hulls?.map((h) => {
          return (
            <div
              key={`bg-${h.cluster_id}`}
              id={`semantic-region-${h.cluster_id}`}
              className="absolute left-0 top-0 rounded-full"
              style={{
                width: 200, height: 200,
                background: `radial-gradient(circle, rgba(79,107,246,0.06) 0%, rgba(79,107,246,0) 70%)`,
                filter: 'blur(30px)',
                transformOrigin: 'center center',
                willChange: 'transform'
              }}
            />
          )
        })}
      </div>

      <div ref={containerRef} className="absolute inset-0 z-10" />

      {/* Semantic Region Labels */}
      <div className="absolute inset-0 pointer-events-none z-20">
        {dataset?.hulls?.map((h) => {
          const mainConcept = h.label || h.top_concepts?.[0] || `Cluster ${h.cluster_id}`
          const secondary = h.top_concepts?.[1] || ''
          return (
            <div
              key={`label-${h.cluster_id}`}
              ref={(el) => (labelsRef.current[h.cluster_id] = el)}
              className="absolute left-0 top-0 transition-opacity duration-300"
              style={{ transformOrigin: 'center center', willChange: 'transform, opacity' }}
            >
              <div className="flex flex-col items-center pointer-events-auto">
                <div className="px-3 py-1.5 glass-panel rounded-xl text-[11px] font-semibold text-slate-700 shadow-sm cursor-pointer hover:bg-white transition-colors border border-slate-200/50">
                  {mainConcept}
                </div>
                {secondary && (
                  <div className="text-[9px] font-medium text-slate-400 mt-1 uppercase tracking-wider drop-shadow-sm">
                    {secondary}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Hover Tooltip */}
      {hoverNode && (
        <div 
          className="absolute z-50 glass-panel p-4 w-[280px] pointer-events-none fade-in rounded-2xl"
          style={{
            left: hoverPos.x + 15,
            top: hoverPos.y - 15,
          }}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-sm">
              {hoverNode.project_name?.[0] || '?'}
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900 leading-tight">
                {hoverNode.project_name}
              </h4>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium mt-0.5">
                {hoverNode.archetype || 'Unknown'}
              </p>
            </div>
          </div>
          {hoverNode.one_liner && (
            <p className="text-[11px] text-slate-600 leading-relaxed mt-2 line-clamp-3">
              {hoverNode.one_liner}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
