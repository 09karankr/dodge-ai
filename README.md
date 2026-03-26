# Dodge AI: SAP O2C Graph Intelligence & Query System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React: 18/19](https://img.shields.io/badge/React-18/19-61dafb.svg)](https://reactjs.org/)
[![Neo4j: 5.x](https://img.shields.io/badge/Neo4j-5.x-4581c3.svg)](https://neo4j.com/)

**Dodge AI** is a high-performance, conversational graph intelligence platform built to navigate and analyze complex SAP **Order-to-Cash (O2C)** datasets. By combining the relational power of **Neo4j** with the natural language reasoning of **Gemini 1.5 Pro**, it enables users to query business processes as easily as asking a question.

---

## ✨ Key Features

- 🧠 **Natural Language to Cypher**: Ask complex questions in plain English ("Show me the flow for Order 740506") and get instant graph visualizations.
- 🎨 **Immersive 3D Visualization**: High-performance canvas-based rendering with radial gradients, dynamic labels, and rhythmic **Red Pulse** transaction particles.
- 🧩 **Categorical Force Clustering**: Physically reorganize the graph into business "neighborhoods" (Sales, Delivery, Billing, etc.) using real-time D3 force-fields.
- 🔍 **Deep Anomaly Detection**: Built-in heuristic queries to detect "Ghost Deliveries," "Pending Revenue," and "Orphaned Invoices."
- 📍 **Smart Navigation**: Synchronized chat-to-graph transitions—click a mention in the chat to smoothly glide the camera to the corresponding node.

---

## 🏗️ Tech Stack

- **Frontend**: React 19, TypeScript, Vite, `react-force-graph-2d`, `d3-force`.
- **Backend**: FastAPI (Python), `neo4j-driver`.
- **Database**: Neo4j (Graph Database).
- **Intelligence**: Gemini 1.5 Pro via OpenRouter.
- **Styling**: Modern Glassmorphism with Vanilla CSS.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js v18+
- Neo4j Instance (running on `bolt://localhost:7687`)

### Setup
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Dodge-ai
   ```
2. **Configure Environment**:
   Create a `.env` file in the `backend/` directory:
   ```env
   OPENROUTER_API_KEY=your_key_here
   NEO4J_PASSWORD=your_password
   ```
3. **Launch the platform**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
4. **Access the application**:
   Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📊 Data Taxonomy
The system currently models **19 SAP datasets**, creating a unified process lineage across:
- **Demand**: Sales Orders, Line Items, Schedules.
- **Logistics**: Delivery Documents, Packing Items, Plants.
- **Finance**: Billing Documents, Accounting Entries, Payments.

---

## 📖 Documentation
- [View Full Technical Documentation](documentation.md)
- [Database Schema & Taxonomy](database_documentation.md)
- [Deep-Dive Internal Manual](ULTRA_DETAILED_DOCUMENTATION.md)

---
*Developed by Karan Kumar*
