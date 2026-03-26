import { useCallback, useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceX, forceY, forceCollide } from 'd3-force';

export default function GraphView({
  graphData,
  highlightNodes,
  showLabels = true,
  clusterMode = false,
  importanceMap = {},
  islandIds = new Set()
}: {
  graphData: any,
  highlightNodes: Set<string>,
  showLabels?: boolean,
  clusterMode?: boolean,
  importanceMap?: Record<string, number>,
  islandIds?: Set<string>
}) {
  const fgRef = useRef<any>(null);
  const [hoverNode, setHoverNode] = useState<any>(null);
  const [currentZoom, setCurrentZoom] = useState(1);

  useEffect(() => {
    if (fgRef.current) {
      (window as any).fgRef = fgRef.current;
    }
  });

  useEffect(() => {
    if (fgRef.current && graphData?.nodes && graphData.nodes.length > 0) {
      setTimeout(() => {
        if (fgRef.current) {
          fgRef.current.zoomToFit(400, 50);
          setCurrentZoom(fgRef.current.zoom());
        }
      }, 500);
    }
  }, [graphData]);

  // Categorical Force Clustering Logic (Defensive Implementation)
  useEffect(() => {
    if (!fgRef.current) return;

    try {
      console.log("GraphView: Toggling clustering mode:", clusterMode);

      // Warm up the simulation safely
      if (typeof fgRef.current.d3ReheatSimulation === 'function') {
        fgRef.current.d3ReheatSimulation();
      }

      const centers: Record<string, { x: number, y: number }> = {
        'SalesOrder': { x: -300, y: -250 },
        'OrderItem': { x: -150, y: -250 },
        'Delivery': { x: 300, y: -250 },
        'DeliveryItem': { x: 450, y: -250 },
        'BillingDocument': { x: 300, y: 250 },
        'InvoiceItem': { x: 450, y: 250 },
        'Payment': { x: -300, y: 250 },
        'JournalEntry': { x: -450, y: 250 },
        'Customer': { x: -600, y: 0 },
        'Product': { x: 600, y: 0 },
        'Plant': { x: 0, y: 450 }
      };

      if (clusterMode) {
        // Apply force objects from d3-force with safety accessors
        fgRef.current.d3Force('x', forceX((node: any) => {
          if (!node || !node.group) return 0;
          return centers[node.group]?.x || 0;
        }).strength(0.15));

        fgRef.current.d3Force('y', forceY((node: any) => {
          if (!node || !node.group) return 0;
          return centers[node.group]?.y || 0;
        }).strength(0.15));

        fgRef.current.d3Force('collide', forceCollide((node: any) => {
          const importance = (importanceMap && node.id && importanceMap[String(node.id)]) || 0;
          return 15 + (importance / 2);
        }));
      } else {
        // Reset forces to standard organic layout
        fgRef.current.d3Force('x', null);
        fgRef.current.d3Force('y', null);
        fgRef.current.d3Force('collide', forceCollide(12));
      }

      // Correct way to reheat simulation safely
      const sim = fgRef.current.d3Simulation();
      if (sim && typeof sim.alpha === 'function' && typeof sim.restart === 'function') {
        sim.alpha(0.3).restart();
      }
    } catch (err) {
      console.error("GraphView: Critical error during clustering update:", err);
      // Fallback: Just restart the simulation without new forces to avoid crash
      fgRef.current?.d3ReheatSimulation?.();
    }
  }, [clusterMode, importanceMap]);

  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    if (node.x === undefined || node.y === undefined || isNaN(node.x) || isNaN(node.y)) return;

    const isHighlighted = highlightNodes?.has?.(String(node.id)) || false;
    const isHovered = hoverNode === node;
    const isIsland = islandIds?.has?.(String(node.id)) || false;
    const importance = (importanceMap && importanceMap[String(node.id)]) || 0;

    // ZOOM-AWARE SIZING
    const baseSize = isHighlighted ? 5 : (isHovered ? 4 : 2.5);
    const zoomFactor = Math.min(1, 2 / globalScale);

    let size = baseSize * zoomFactor;
    if (importance > 0) {
      const importanceBonus = Math.min(6, (importance / 4)) * zoomFactor;
      size += importanceBonus;
    }

    size = Math.max(1, Math.min(12, size));
    if (clusterMode && !isHighlighted && importance === 0) size = 4 * zoomFactor;

    let baseColor = '#60a5fa';
    if (node.group === 'SalesOrder') baseColor = '#f59e0b';
    else if (node.group === 'Delivery' || node.group === 'DeliveryItem') baseColor = '#10b981';
    else if (node.group === 'BillingDocument' || node.group === 'InvoiceItem') baseColor = '#ec4899';
    else if (node.group === 'Payment') baseColor = '#6366f1';
    else if (node.group === 'JournalEntry') baseColor = '#a855f7';
    else if (node.group === 'Customer') baseColor = '#38bdf8';
    else if (node.group === 'Product') baseColor = '#fb923c';
    else if (node.group === 'Plant') baseColor = '#94a3b8';

    const gradient = ctx.createRadialGradient(node.x, node.y, 0.1, node.x, node.y, Math.max(0.1, size));
    const fill = isHighlighted ? '#1d4ed8' : baseColor;
    gradient.addColorStop(0, isHighlighted ? '#60a5fa' : (isHovered ? '#ffffff' : fill));
    gradient.addColorStop(1, fill);

    if (isHighlighted || isHovered) {
      ctx.shadowColor = fill;
      ctx.shadowBlur = 10 / globalScale;
    }

    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
    ctx.fillStyle = gradient;
    ctx.fill();

    let stroke = isHighlighted ? '#1e3a8a' : (clusterMode ? '#ffffff' : baseColor);
    if (isIsland && !isHighlighted) stroke = '#ffffff';

    ctx.strokeStyle = stroke;
    ctx.lineWidth = (isHighlighted || isIsland || isHovered) ? (2 / globalScale) : (0.5 / globalScale);
    ctx.stroke();

    ctx.shadowBlur = 0;

    if (clusterMode && !isHighlighted && !isIsland) {
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 1.5, 0, 2 * Math.PI, false);
      ctx.fill();
    }

    const labelThreshold = (isHighlighted || isHovered) ? 0.2 : (clusterMode ? 0.6 : 1.2);

    if (showLabels && globalScale > labelThreshold) {
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const targetFontSize = 11;
      const fontSize = targetFontSize / globalScale;
      const finalFontSize = Math.min(8, fontSize);

      ctx.font = `${(isHighlighted || isHovered) ? '600' : '500'} ${finalFontSize}px Inter, system-ui, sans-serif`;
      const labelText = node.label || String(node.id);
      const labelY = node.y + (size + finalFontSize / 2 + 2);

      if (isHighlighted || isHovered) {
        ctx.fillStyle = '#0f172a';
        ctx.shadowColor = 'rgba(255,255,255,0.8)';
        ctx.shadowBlur = 4;
      } else {
        ctx.fillStyle = '#334155';
        ctx.shadowBlur = 0;
      }

      ctx.fillText(labelText, node.x, labelY);
      ctx.shadowBlur = 0;
    }
  }, [highlightNodes, showLabels, clusterMode, importanceMap, islandIds, hoverNode]);

  return (
    <div style={{ height: '100%', width: '100%' }}>
      {graphData?.nodes?.length > 0 ? (
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node: any) => {
            let tt = `<div class="graph-tooltip"><strong>${node.label || node.id || node.group}</strong>`;
            tt += `Entity: <span>${node.group}</span><br/>`;
            if (node.props) {
              Object.entries(node.props).forEach(([k, v]) => {
                if (String(v).length > 0) tt += `${k}: <span>${v}</span><br/>`;
              });
            }
            tt += `</div>`;
            return tt;
          }}
          nodeCanvasObject={drawNode}
          onNodeHover={setHoverNode}
          onZoom={(transform) => setCurrentZoom(transform.k)}

          // Link Visuals
          linkColor={(link: any) => {
            const s = String(link.source.id || link.source);
            const t = String(link.target.id || link.target);
            const isHighlighted = (highlightNodes?.has?.(s) || highlightNodes?.has?.(t));
            const isHovered = (hoverNode === link.source || hoverNode === link.target);
            return (isHighlighted || isHovered) ? '#3b82f6' : 'rgba(148, 163, 184, 0.4)';
          }}
          linkWidth={(link: any) => {
            const isHovered = (hoverNode === link.source || hoverNode === link.target);
            return isHovered ? 2 : 1;
          }}
          linkCurvature={0}
          linkDirectionalArrowLength={Math.max(1, 4 / currentZoom)}
          linkDirectionalArrowRelPos={1}
          linkDirectionalParticles={(link: any) => {
            const isHovered = (hoverNode === link.source || hoverNode === link.target);
            return isHovered ? 4 : 0;
          }}
          linkDirectionalParticleSpeed={0.0025}
          linkDirectionalParticleWidth={4}
          linkDirectionalParticleColor={() => '#e80b0bff'}

          backgroundColor="#f8fafc"
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          cooldownTicks={100}
          onNodeClick={(node) => {
            if (fgRef.current) {
              fgRef.current.centerAt(node.x, node.y, 800);
              fgRef.current.zoom(8, 1500);
            }
          }}
        />
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
          Initialize Graph to view visualization
        </div>
      )}
    </div>
  )
}
