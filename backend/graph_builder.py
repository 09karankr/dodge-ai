import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "password"))
_driver = None

def get_driver():
    global _driver
    if not _driver:
        _driver = GraphDatabase.driver(URI, auth=AUTH)
    return _driver

def serialize_neo4j(obj):
    from neo4j.graph import Node, Relationship
    if isinstance(obj, Node) or isinstance(obj, Relationship):
        return dict(obj)
    if isinstance(obj, dict):
        return {k: serialize_neo4j(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_neo4j(i) for i in obj]
    return obj

def execute_cypher(query, params=None):
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run(query, params or {})
            data = [dict(record) for record in result]
            return serialize_neo4j(data)
    except Exception as e:
        return {"error": str(e)}

def build_graph_from_ids(ids_to_check):
    """
    Returns nodes and links for the UI context graph.
    If ids_to_check is empty, returns the whole graph.
    Otherwise, returns the connected subgraph involving those IDs.
    """
    driver = get_driver()
    nodes = {}
    edges_set = set()
    links = []

    def add_node(n):
        if not n: return
        nid = str(n.get("id"))
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": n.get("label", nid), "group": n.get("group", "Unknown"), "props": dict(n)}

    try:
        with driver.session() as session:
            if not ids_to_check:
                # User specifically requested the FULL graph without any limits
                res = session.run("MATCH (n)-[r]->(m) RETURN n, type(r) as rel, m")
            else:
                # Get sub-graph (1-hop) for all keys
                # We do undirected match but return directed paths using startNode/endNode
                # To maintain explicit direction:
                res = session.run("""
                MATCH (n)-[r]->(m)
                WHERE n.id IN $keys OR m.id IN $keys
                RETURN n, type(r) as rel, m
                """, keys=ids_to_check)
                
            for record in res:
                n = record.get("n")
                m = record.get("m")
                rel = record.get("rel")
                if n: add_node(n)
                if m: add_node(m)
                if n and m and rel:
                    nid = str(n.get("id"))
                    mid = str(m.get("id"))
                    edge_key = f"{nid}-{rel}-{mid}"
                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        links.append({"source": nid, "target": mid, "label": rel})
                        
    except Exception as e:
        print("Neo4j Error", e)

    return {"nodes": list(nodes.values()), "links": links}

def run_deep_analysis():
    """Performs Centrality and basic Community analysis using Cypher."""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        # 1. Centrality (Importance) - Count total degree of nodes
        centrality = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            RETURN n.id as id, count(r) as importance
        """)
        importance_map = {str(r["id"]): r["importance"] for r in centrality}

        # 2. Find High Importance Nodes
        top_ids = sorted(importance_map.keys(), key=lambda k: importance_map[k], reverse=True)[:10]

        # 3. Find "Islands" (Nodes with very few connections)
        islands = [id for id, imp in importance_map.items() if imp <= 1]

        # Construct a report
        summary = f"**Deep Analysis Result:**\n"
        summary += f"- **Centrality**: Identified {len(top_ids)} high-transaction nodes (Hubs).\n"
        summary += f"- **Orphans**: Found {len(islands)} isolated process steps that may require attention.\n"
        
        return {
            "summary": summary,
            "importance": importance_map,
            "key_ids": top_ids + islands,
            "islands": islands
        }

def run_anomaly_analysis():
    """
    Performs specialized queries to find process bottlenecks/anomalies:
    1. Cancelled BillingDocuments
    2. SalesOrders without Deliveries (Pending)
    3. Deliveries without BillingDocuments (Unbilled)
    """
    driver = get_driver()
    key_ids = set()
    anomalies = []

    try:
        with driver.session() as session:
            # 1. Cancelled Invoices
            res1 = session.run("MATCH (b:BillingDocument) WHERE b.isCancelled = true OR b.status = 'CANCELLED' RETURN b.id as id")
            c1 = 0
            for r in res1:
                key_ids.add(str(r["id"]))
                c1 += 1
            if c1 > 0: anomalies.append(f"Found {c1} **Cancelled Billing Documents**.")

            # 2. Orders without Deliveries
            res2 = session.run("MATCH (o:SalesOrder) WHERE NOT (o)-[:DELIVERED_AS]->(:Delivery) RETURN o.id as id")
            c2 = 0
            for r in res2:
                key_ids.add(str(r["id"]))
                c2 += 1
            if c2 > 0: anomalies.append(f"Found {c2} **Pending Sales Orders** (no delivery).")

            # 3. Deliveries without Billing
            res3 = session.run("MATCH (d:Delivery) WHERE NOT (d)-[:BILLED_AS]->(:BillingDocument) RETURN d.id as id")
            c3 = 0
            for r in res3:
                key_ids.add(str(r["id"]))
                c3 += 1
            if c3 > 0: anomalies.append(f"Found {c3} **Unbilled Deliveries**.")

    except Exception as e:
        return {"summary": f"Analysis Error: {str(e)}", "key_ids": []}

    summary = "### Graph Anomaly Report\n\n" + "\n".join([f"- {a}" for a in anomalies])
    summary += "\n\nRelevant nodes have been **highlighted** in the graph for inspection."
    
    return {"summary": summary, "key_ids": list(key_ids)}
