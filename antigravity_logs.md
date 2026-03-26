# Dodge AI: Engineering Prompts Log

**Authored by:** Karan Kumar  
**Project:** Dodge AI (SAP O2C Graph Intelligence)  
**Creation Date:** March 2026  

This document serves as an archive of the critical architectural and engineering prompts used to collaborate with the AI (Antigravity System) in developing the Dodge AI platform from scratch to production.

---

## 1. Foundation & Ingestion Phase
* **Prompt:** "Analyze the `sap-o2c-data` directory and build a robust Neo4j data ingestion script in Python."
* **Prompt:** "We need a FastAPI backend that incorporates Gemini Pro to dynamically translate natural language questions into executable Neo4j Cypher queries."
* **Prompt:** "Ensure the LLM recursively extracts exact Neo4j Node IDs from the Cypher results so the frontend knows exactly which process nodes to highlight."

## 2. Frontend UX & React Architecture Phase
* **Prompt:** "Set up a Vite-backed React application using a premium, minimalistic dark theme with glassmorphism UI elements."
* **Prompt:** "Integrate `react-force-graph-2d` for the central visualization. The nodes should be rendered not just as flat circles, but as 3D-effect spheres with radial gradients."
* **Prompt:** "Implement a resizable drag-handle sidebar so the user can control the width of the chatbot."

## 3. Kinetic Animation & Physics Refinement (The "Red Pulse")
* **Prompt:** "Whenever I hover on some nodes, few particles go in or out of it very fast. Make it slow and also change those particle colors." *(Led to the rhythmic Cyan/Electric Flow).*
* **Prompt:** "What do the directions of those particles mean?" *(Led to establishing the directional transaction flow mapping).*
* **Prompt:** "Can we also name the edges? Will it be a good idea?"
* **Prompt:** "Make the lines straight." *(Replaced D3 curved links with straight architectural edges for enterprise clarity).*

## 4. D3 Physics Debugging & Clustering
* **Prompt:** "When I click 'Enable Clustering', it makes the page white, please fix the issue."
* **Prompt:** "Still, when I click on 'Enable Clustering', the whole website goes to a white screen, please try to find and fix this issue." *(Led to wrapping the D3 forces in a defensive `try-catch` block and properly instantiating `d3.forceX`).*
* **Prompt:** "Rename the browser tab name to something meaningful instead of 'temp'."

## 5. Intelligence Modules & Documentation
* **Prompt:** "Add a 'Deep Analysis' endpoint to detect process anomalies like orphaned deliveries and pending revenue."
* **Prompt:** "Now I want full documentation in full detail about this website in a `.md` file."
* **Prompt:** "I want it to be *very* detailed." *(Led to `ULTRA_DETAILED_DOCUMENTATION.md` internal wiki).*
* **Prompt:** "Create a `README.md` for this project."

## 6. GitHub Migration & Cloud Deployment (Render + Neo4j Aura)
* **Prompt:** "Now I want to push this repo, from where I want to deploy it on Render."
* **Prompt:** "I think the neo4j is not using the database online... The deployed frontend gives an error: Could not connect to the Neo4j backend. Please check if the server is running on port 8000." *(Led to fixing the frontend `VITE_API_BASE` for production rendering).*

---
*Generated mathematically from the Antigravity conversation matrix.*
