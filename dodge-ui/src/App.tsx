import { useState, useEffect, useMemo, useCallback } from 'react';
import GraphView from './GraphView';
import ChatPanel from './ChatPanel';
import type { ChatMessage } from './ChatPanel';
import { Columns, Minimize2, Layers, Folder } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const DATASETS = [
  "billing_document_cancellations",
  "billing_document_headers",
  "billing_document_items",
  "business_partner_addresses",
  "business_partners",
  "customer_company_assignments",
  "customer_sales_area_assignments",
  "journal_entry_items_accounts_receivable",
  "outbound_delivery_headers",
  "outbound_delivery_items",
  "payments_accounts_receivable",
  "plants",
  "product_descriptions",
  "product_plants",
  "product_storage_locations",
  "products",
  "sales_order_headers",
  "sales_order_items",
  "sales_order_schedule_lines"
];

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [showGranular, setShowGranular] = useState(true);
  const [clusterMode, setClusterMode] = useState(false);
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'bot',
      text: 'Hi! I can help you explore the SAP Order-to-Cash context graph and query relationships between entities.',
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [chatWidth, setChatWidth] = useState(350);
  const [resizingSide, setResizingSide] = useState<'sidebar' | 'chat' | null>(null);

  const startResizing = useCallback((side: 'sidebar' | 'chat') => {
    setResizingSide(side);
  }, []);

  const stopResizing = useCallback(() => {
    setResizingSide(null);
  }, []);

  const resize = useCallback((mouseMoveEvent: MouseEvent) => {
    if (resizingSide === 'sidebar') {
      const newWidth = mouseMoveEvent.clientX;
      if (newWidth > 150 && newWidth < 600) {
        setSidebarWidth(newWidth);
      }
    } else if (resizingSide === 'chat') {
      const newWidth = window.innerWidth - mouseMoveEvent.clientX;
      if (newWidth > 300 && newWidth < 800) {
        setChatWidth(newWidth);
      }
    }
  }, [resizingSide]);

  useEffect(() => {
    document.title = "Dodge AI: O2C Graph Explorer";
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);

  useEffect(() => {
    setIsLoading(true);
    fetch(`${API_BASE}/api/graph/init`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
        return r.json();
      })
      .then(data => {
        setGraphData(data);
        setIsLoading(false);
      })
      .catch(e => {
        console.error("Fetch error:", e);
        setMessages(prev => [...prev, { id: 'error-init', sender: 'bot', text: `Error: Could not connect to the Neo4j backend at ${API_BASE}.` }]);
        setIsLoading(false);
      });
  }, []);

  const handleSend = async (text: string) => {
    const userMsg: ChatMessage = { id: Date.now().toString(), sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // Include history context mapping
      const history = messages
          .filter(m => m.id !== '1') // skip default initial
          .map(m => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.text }));
      history.push({ role: 'user', content: text });

      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, history })
      });
      const data = await res.json();
      
      if (data.graphData && data.graphData.nodes) {
        setGraphData(data.graphData);
      }
      
      if (data.key_ids) {
        setHighlightNodes(new Set(data.key_ids.map(String)));
      } else {
        setHighlightNodes(new Set());
      }
      
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.textResponse || "Sorry, I couldn't find an answer for that.",
        cypherQuery: data.sql
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: 'Error connecting to backend.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const [importanceMap, setImportanceMap] = useState<Record<string, number>>({});
  const [islandIds, setIslandIds] = useState<Set<string>>(new Set());

  const handleDeepAnalyze = async () => {
    setIsLoading(true);
    setMessages(prev => [...prev, { id: 'deep-analyze', sender: 'user', text: '📊 Perform Deep Centrality & Community Analysis' }]);
    try {
      const res = await fetch(`${API_BASE}/api/analysis/deep`);
      const data = await res.json();
      
      setImportanceMap(data.importance || {});
      setIslandIds(new Set(data.islands || []));
      
      if (data.key_ids) {
        setHighlightNodes(new Set(data.key_ids.map(String)));
      }
      
      setMessages(prev => [...prev, { 
        id: 'deep-analyze-res', 
        sender: 'bot', 
        text: data.summary || "Deep analysis complete. Graph nodes have been scaled by importance."
      }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { id: 'deep-err', sender: 'bot', text: 'Error running deep analysis.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setIsLoading(true);
    setMessages(prev => [...prev, { id: 'analyze', sender: 'user', text: '🔍 Perform Advanced Process Anomaly Analysis' }]);
    try {
      const res = await fetch(`${API_BASE}/api/analysis/anomalies`);
      const data = await res.json();
      
      if (data.key_ids) {
        setHighlightNodes(new Set(data.key_ids.map(String)));
      }
      
      setMessages(prev => [...prev, { 
        id: 'analyze-res', 
        sender: 'bot', 
        text: data.summary || "Analysis complete. Relevant nodes have been highlighted."
      }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { id: 'analyze-err', sender: 'bot', text: 'Error running advanced analysis.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const activeHighlightNodes = useMemo(() => {
    const combined = new Set(highlightNodes);
    if (selectedDataset) {
       // Comprehensive mapping of every dataset to its graph node group(s)
       const datasetToGroups: Record<string, string[]> = {
         'sales_order_headers': ['SalesOrder'],
         'sales_order_items': ['OrderItem'],
         'sales_order_schedule_lines': ['SalesOrder', 'OrderItem'],
         'outbound_delivery_headers': ['Delivery'],
         'outbound_delivery_items': ['DeliveryItem'],
         'billing_document_headers': ['BillingDocument'],
         'billing_document_items': ['InvoiceItem'],
         'billing_document_cancellations': ['BillingDocument'],
         'payments_accounts_receivable': ['Payment'],
         'journal_entry_items_accounts_receivable': ['JournalEntry'],
         'business_partners': ['Customer'],
         'business_partner_addresses': ['Address'],
         'customer_company_assignments': ['Customer'],
         'customer_sales_area_assignments': ['Customer'],
         'products': ['Product'],
         'product_descriptions': ['Product'],
         'product_plants': ['Product', 'Plant'],
         'product_storage_locations': ['Product', 'Plant'],
         'plants': ['Plant'],
       };

       const targetGroups = datasetToGroups[selectedDataset] || [];
       if (targetGroups.length > 0) {
          graphData.nodes.forEach((n: any) => {
             if (targetGroups.includes(n.group)) combined.add(String(n.id));
          });
       }
    }
    return combined;
  }, [highlightNodes, selectedDataset, graphData]);


  return (
    <div className="app-container">
      <div className="top-nav">
        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="icon-btn" title="Toggle Sidebar">
           <Columns size={18} />
        </button>
        {/* Updated branding based on PDF task details */}
        Project / <strong>Graph-Based O2C Query System</strong>
      </div>
      <div className="main-content">
        {isSidebarOpen && (
          <>
            <div className="sidebar" style={{ width: sidebarWidth }}>
               <div className="sidebar-title">Datasets</div>
               <div className="sidebar-list">
                  <div 
                    className={`sidebar-item ${selectedDataset === null ? 'active' : ''}`}
                    onClick={() => setSelectedDataset(null)}
                  >
                     <Folder size={14} /> Full Graph (No Filter)
                  </div>
                  {DATASETS.map(ds => (
                    <div 
                      key={ds}
                      className={`sidebar-item ${selectedDataset === ds ? 'active' : ''}`}
                      onClick={() => setSelectedDataset(ds)}
                    >
                       <Folder size={14} /> {ds}
                    </div>
                  ))}
               </div>
            </div>
            <div className="resizer" onMouseDown={() => startResizing('sidebar')} />
          </>
        )}
        <div className="graph-section">
          <div className="graph-buttons">
            <button className={`graph-btn ${clusterMode ? 'active' : ''}`} onClick={() => setClusterMode(!clusterMode)}>
               <Layers size={14}/> {clusterMode ? 'Disable Clustering' : 'Enable Clustering'}
            </button>
            <button className="graph-btn dark" onClick={handleAnalyze} disabled={isLoading}>
               <Layers size={14}/> Run Anomaly Analysis
            </button>
            <button className="graph-btn dark" style={{ background: '#4338ca' }} onClick={handleDeepAnalyze} disabled={isLoading}>
               <Layers size={14}/> Run Deep Analysis
            </button>
            <button className={`graph-btn ${showGranular ? 'active' : ''}`} onClick={() => setShowGranular(!showGranular)}>
               <Layers size={14}/> {showGranular ? 'Hide Labels' : 'Show Labels'}
            </button>
            <button className="graph-btn" onClick={() => setIsChatOpen(!isChatOpen)}>
               <Minimize2 size={14}/> {isChatOpen ? 'Maximize Viewer' : 'Restore Layout'}
            </button>
          </div>
          <GraphView 
            graphData={graphData} 
            highlightNodes={activeHighlightNodes} 
            showLabels={showGranular} 
            clusterMode={clusterMode} 
            importanceMap={importanceMap}
            islandIds={islandIds}
          />
        </div>
        {isChatOpen && (
          <>
            <div className="resizer chat" onMouseDown={() => startResizing('chat')} />
            <ChatPanel 
              messages={messages} 
              onSend={handleSend} 
              isLoading={isLoading} 
              width={chatWidth}
            onNodeClick={(id) => {
              console.log("App: Node navigation requested for ID:", id);
              const fg = (window as any).fgRef;
              if (!fg) {
                console.error("App: Graph reference (fgRef) not found on window.");
                return;
              }

              const internalData = fg.getGraphData();
              const targetNode = internalData.nodes.find((n: any) => String(n.id) === String(id));
              
              if (targetNode) {
                console.log("App: Found target node in graph simulation at:", targetNode.x, targetNode.y);
                setHighlightNodes(new Set([String(id)]));
                
                // Centering and zooming with a slight delay to ensure smooth transition
                fg.centerAt(targetNode.x, targetNode.y, 1000);
                fg.zoom(8, 1500);
              } else {
                console.warn("App: Requested node ID not found in simulation data:", id);
                // Fallback to state search if simulation hasn't started
                const stateNode = graphData.nodes.find((n: any) => String(n.id) === String(id));
                if (stateNode) setHighlightNodes(new Set([String(id)]));
              }
            }}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
