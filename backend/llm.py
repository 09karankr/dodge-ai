import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from graph_builder import execute_cypher

load_dotenv()

client = None
if os.environ.get("OPENROUTER_API_KEY"):
    client = OpenAI(
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

MODEL_NAME = os.environ.get("MODEL_NAME", "google/gemini-3.1-flash-lite-preview")

SCHEMA = """
Graph Schema in Neo4j:
Nodes: 
  Customer (id, name, fullName, category, isBlocked)
  Address (id, city, country, region, postalCode, street)
  SalesOrder (id, totalNetAmount, currency, creationDate, deliveryStatus, paymentTerms, soldToParty)
  OrderItem (id, orderId, item, material, quantity, netAmount, plant)
  Delivery (id, creationDate, goodsMovementStatus, pickingStatus, shippingPoint)
  DeliveryItem (id, deliveryId, quantity, unit, plant, storageLocation)
  BillingDocument (id, totalNetAmount, currency, creationDate, isCancelled, status, companyCode, accountingDocument, soldToParty)
  InvoiceItem (id, billingId, material, quantity, netAmount)
  JournalEntry (id, amount, docType, glAccount, refDoc)
  Payment (id, amount, currency, clearingDate, customer, clearingDoc)
  Product (id, name, type, productGroup, baseUnit)
  Plant (id, name)

Relationships (Edges):
  (Customer)-[:PLACED]->(SalesOrder)
  (Customer)-[:HAS_ADDRESS]->(Address)
  (Customer)-[:RECEIVED]->(Delivery)
  (SalesOrder)-[:HAS_ITEM]->(OrderItem)
  (OrderItem)-[:OF_MATERIAL]->(Product)
  (OrderItem)-[:FULFILLED_BY]->(DeliveryItem)
  (Product)-[:STORED_AT]->(Plant)
  (SalesOrder)-[:DELIVERED_AS]->(Delivery)
  (Delivery)-[:CONTAINS_ITEM]->(DeliveryItem)
  (DeliveryItem)-[:SHIPPED_FROM]->(Plant)
  (DeliveryItem)-[:BILLED_FROM]->(InvoiceItem)
  (Delivery)-[:BILLED_AS]->(BillingDocument)
  (BillingDocument)-[:HAS_ITEM]->(InvoiceItem)
  (BillingDocument)-[:GENERATES]->(JournalEntry)
  (BillingDocument)-[:PAID_BY]->(Payment)
  (JournalEntry)-[:POSTED_TO]->(Customer)
"""

SYSTEM_PROMPT_1 = """
You are a highly capable AI built to query an SAP Order-to-Cash Neo4j database using Cypher.
You must reject any question NOT related to the business dataset (e.g., creative writing, general knowledge). 
If unrelated, set is_relevant to false.
Otherwise, translate the user's question into a clean Neo4j Cypher query.

CRITICAL: Do NOT use Cypher parameters (e.g., $customer_name). 
Always use literal values or strings directly in the Cypher query (e.g., 'Customer A' instead of $name).
If the user's question is generic (e.g., "List all products"), do not add filters that require parameters.

Respond STRICTLY in JSON:
{
  "is_relevant": true/false,
  "rejection_message": "Only fill if is_relevant is false.",
  "cypher": "MATCH ... RETURN ... LIMIT 100",
  "key_ids": ["If looking for a specific flow or entity, put the graph Node IDs here, else empty"]
}
"""

SYSTEM_PROMPT_2 = """
You are a helpful Data Analyst. You are given a user's question, the Cypher query used, and the JSON results from the graph database.
Your job is to write a highly legible, beautifully structured natural language answer.

Follow these rules:
1. Use Markdown for structure.
2. If there are multiple items, ALWAYS use a bulleted list.
3. Use bolding (**Text**) for key terms, categorization, or totals.
4. **INTERACTIVE LINKS**: When you mention a specific entity (Product name, Customer name, Order ID, etc.) that appears in the JSON result, ALWAYS wrap it in a special link format: `[Entity Name](id:ENTITY_ID)`.
   - The `ENTITY_ID` MUST be the exact 'id' field value from the JSON result for that specific entity.
   - Example: "The total for [Order 740506](id:740506) is $500."
   - Example: "Product [SUNSCREEN](id:3001456) was shipped from [Plant 1001](id:1001)."
5. If appropriate, group items by category.
6. Keep it concise but professional.
7. Do NOT mention the Cypher query or technical database terms.
"""

def generate_answer(user_question: str, history: list = None):
    history = history or []
    if not client:
        return {
            "answer": "OPENROUTER_API_KEY is not set in the .env file.",
            "sql": "",
            "key_ids": []
        }
        
    hist_text = ""
    for msg in history[-5:]:
        hist_text += f"[{msg['role']}]: {msg['content']}\n"
        
    # Pass 1: Get Cypher
    prompt1 = f"{SYSTEM_PROMPT_1}\n\nSchema:\n{SCHEMA}\n\nConversation History:\n{hist_text}\n\nUser Question: {user_question}"
    try:
        r1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt1}]
        )
        text = r1.choices[0].message.content.strip()
        if text.startswith("```json"): text = text[7:-3]
        elif text.startswith("```"): text = text[3:-3]
        
        parsed = json.loads(text)
    except Exception as e:
        return {"answer": f"Failed to parse LLM intent: {str(e)}", "key_ids": []}

    if not parsed.get("is_relevant", True):
        return {
            "answer": parsed.get("rejection_message", "This system only answers dataset-related questions."),
            "sql": "",
            "key_ids": []
        }
        
    cypher = parsed.get("cypher", "")
    key_ids = parsed.get("key_ids", [])
    
    if cypher:
        data = execute_cypher(cypher)
        if isinstance(data, dict) and "error" in data:
            return {"answer": f"Database Error: {data['error']}", "sql": cypher, "key_ids": key_ids}
        
        # Pass 2: Natural Language Generation
        prompt2 = f"{SYSTEM_PROMPT_2}\nConversation History\n{hist_text}\nUser Question: {user_question}\nCypher Result: {json.dumps(data)[:3000]}"
        r2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt2}]
        )
        answer = r2.choices[0].message.content.strip()

        # Extract all 'id' fields from results to ensure highlighting
        def extract_ids(obj, found_ids):
            if isinstance(obj, dict):
                if "id" in obj: 
                    found_ids.add(str(obj["id"]))
                for v in obj.values():
                    extract_ids(v, found_ids)
            elif isinstance(obj, list):
                for i in obj:
                    extract_ids(i, found_ids)

        result_ids = set()
        extract_ids(data, result_ids)
        
        # Merge LLM-suggested IDs with actual result IDs
        final_key_ids = list(set(key_ids) | result_ids)
                        
        return {
            "answer": answer,
            "sql": cypher,
            "key_ids": final_key_ids,
            "data": data
        }
    else:
        return {"answer": "I couldn't formulate a Cypher query for that.", "key_ids": []}
