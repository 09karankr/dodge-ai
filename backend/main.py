from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import llm
import graph_builder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List, Dict, Optional

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/chat")
async def chat_endpoint(request: QueryRequest):
    result = llm.generate_answer(request.query, request.history)
    
    # Fetch Graph Context
    key_ids = result.get("key_ids", [])
    graph_data = graph_builder.build_graph_from_ids(key_ids)
    
    return {
        "textResponse": result.get("answer"),
        "sql": result.get("sql"),
        "graphData": graph_data,
        "key_ids": key_ids
    }

@app.get("/api/analysis/anomalies")
async def analysis_anomalies():
    return graph_builder.run_anomaly_analysis()

@app.get("/api/analysis/deep")
async def analysis_deep():
    return graph_builder.run_deep_analysis()

@app.get("/api/graph/init")
async def graph_init():
    # Return entire graph initially (it's small)
    graph_data = graph_builder.build_graph_from_ids([])
    return graph_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
