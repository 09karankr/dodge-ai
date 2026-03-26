import json
import os
from neo4j import GraphDatabase

URI = "neo4j+s://9fa38957.databases.neo4j.io"
AUTH = ("9fa38957", "nSHvkhY9Tt15Uo0Ufc0xk27HGOJI67ScXedhQFChJjM")

def normalize_item(item_str):
    """Normalize item IDs: '10' -> '000010', '000010' -> '000010'"""
    if not item_str:
        return item_str
    try:
        return str(int(item_str)).zfill(6)
    except ValueError:
        return item_str

def ingest_data():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    with driver.session() as session:
        print("Clearing existing graph...")
        session.run("MATCH (n) DETACH DELETE n")
        
        base_path = "/Users/aryankumar/Desktop/Dodge-ai/sap-o2c-data"

        def read_jsonl(folder):
            path = os.path.join(base_path, folder)
            if not os.path.exists(path): return []
            data = []
            for file in sorted(os.listdir(path)):
                if file.endswith(".jsonl"):
                    with open(os.path.join(path, file), "r") as f:
                        for line in f:
                            data.append(json.loads(line))
            return data

        # ========== PHASE 1: Create ALL Nodes (Batched with UNWIND) ==========
        print("Phase 1: Creating nodes...")

        # 1. Customers
        customers = read_jsonl("business_partners")
        session.run("""
            UNWIND $batch AS c
            MERGE (n:Customer {id: c.id})
            SET n.name = c.name, n.group = 'Customer', n.label = c.name,
                n.category = c.cat, n.fullName = c.full, n.isBlocked = c.blocked
        """, batch=[{
            "id": str(c.get("businessPartner")),
            "name": c.get("businessPartnerName", ""),
            "cat": c.get("businessPartnerCategory", ""),
            "full": c.get("businessPartnerFullName", ""),
            "blocked": c.get("businessPartnerIsBlocked", False)
        } for c in customers])
        print(f"  Customers: {len(customers)}")

        # 2. Addresses
        addresses = read_jsonl("business_partner_addresses")
        session.run("""
            UNWIND $batch AS a
            MERGE (n:Address {id: a.id})
            SET n.group = 'Address', n.label = a.city + ', ' + a.country,
                n.city = a.city, n.country = a.country, n.region = a.region,
                n.postalCode = a.postal, n.street = a.street
        """, batch=[{
            "id": str(a.get("addressId")),
            "city": a.get("cityName", ""), "country": a.get("country", ""),
            "region": a.get("region", ""), "postal": a.get("postalCode", ""),
            "street": a.get("streetName", "")
        } for a in addresses])
        print(f"  Addresses: {len(addresses)}")

        # 3. Plants
        plants = read_jsonl("plants")
        session.run("""
            UNWIND $batch AS p
            MERGE (n:Plant {id: p.id})
            SET n.group = 'Plant', n.label = p.name, n.name = p.name
        """, batch=[{"id": str(p.get("plant")), "name": p.get("plantName", str(p.get("plant")))} for p in plants])
        print(f"  Plants: {len(plants)}")

        # 4. Products
        products = read_jsonl("products")
        descriptions = {p["product"]: p["productDescription"] for p in read_jsonl("product_descriptions")}
        session.run("""
            UNWIND $batch AS p
            MERGE (n:Product {id: p.id})
            SET n.name = p.name, n.group = 'Product', n.label = p.name,
                n.type = p.type, n.productGroup = p.pg, n.baseUnit = p.bu
        """, batch=[{
            "id": str(p.get("product")),
            "name": descriptions.get(p.get("product"), str(p.get("product"))),
            "type": p.get("productType", ""),
            "pg": p.get("productGroup", ""),
            "bu": p.get("baseUnit", "")
        } for p in products])
        print(f"  Products: {len(products)}")

        # 5. Sales Orders
        orders = read_jsonl("sales_order_headers")
        session.run("""
            UNWIND $batch AS o
            MERGE (n:SalesOrder {id: o.id})
            SET n.group = 'SalesOrder', n.label = 'SO: ' + o.id,
                n.totalNetAmount = o.amt, n.currency = o.curr,
                n.creationDate = o.created, n.deliveryStatus = o.dstatus,
                n.paymentTerms = o.terms, n.soldToParty = o.stp
        """, batch=[{
            "id": str(o.get("salesOrder")),
            "amt": o.get("totalNetAmount", ""),
            "curr": o.get("transactionCurrency", ""),
            "created": o.get("creationDate", ""),
            "dstatus": o.get("overallDeliveryStatus", ""),
            "terms": o.get("customerPaymentTerms", ""),
            "stp": o.get("soldToParty", "")
        } for o in orders])
        print(f"  Sales Orders: {len(orders)}")

        # 6. Order Items
        order_items = read_jsonl("sales_order_items")
        session.run("""
            UNWIND $batch AS oi
            MERGE (n:OrderItem {id: oi.iid_full})
            SET n.group = 'OrderItem', n.label = 'Item: ' + oi.iid,
                n.orderId = oi.oid, n.item = oi.iid, n.material = oi.mat,
                n.quantity = oi.qty, n.netAmount = oi.amt, n.plant = oi.plant
        """, batch=[{
            "iid_full": f"{str(oi.get('salesOrder'))}-{normalize_item(str(oi.get('salesOrderItem')))}",
            "oid": str(oi.get("salesOrder")),
            "iid": normalize_item(str(oi.get("salesOrderItem"))),
            "mat": str(oi.get("material", "")),
            "qty": oi.get("requestedQuantity", ""),
            "amt": oi.get("netAmount", ""),
            "plant": oi.get("productionPlant", "")
        } for oi in order_items])
        print(f"  Order Items: {len(order_items)}")

        # 7. Deliveries
        deliveries = read_jsonl("outbound_delivery_headers")
        session.run("""
            UNWIND $batch AS d
            MERGE (n:Delivery {id: d.id})
            SET n.group = 'Delivery', n.label = 'Deliv: ' + d.id,
                n.creationDate = d.created, n.goodsMovementStatus = d.gms,
                n.pickingStatus = d.ps, n.shippingPoint = d.sp
        """, batch=[{
            "id": str(d.get("deliveryDocument")),
            "created": d.get("creationDate", ""),
            "gms": d.get("overallGoodsMovementStatus", ""),
            "ps": d.get("overallPickingStatus", ""),
            "sp": d.get("shippingPoint", "")
        } for d in deliveries])
        print(f"  Deliveries: {len(deliveries)}")

        # 8. Delivery Items
        delivery_items = read_jsonl("outbound_delivery_items")
        session.run("""
            UNWIND $batch AS di
            MERGE (n:DeliveryItem {id: di.iid_full})
            SET n.group = 'DeliveryItem', n.label = 'DelivItem: ' + di.iid,
                n.deliveryId = di.did, n.quantity = di.qty, n.unit = di.unit,
                n.plant = di.plant, n.storageLocation = di.sloc
        """, batch=[{
            "iid_full": f"{str(di.get('deliveryDocument'))}-{normalize_item(str(di.get('deliveryDocumentItem')))}",
            "did": str(di.get("deliveryDocument")),
            "iid": normalize_item(str(di.get("deliveryDocumentItem"))),
            "qty": di.get("actualDeliveryQuantity", ""),
            "unit": di.get("deliveryQuantityUnit", ""),
            "plant": di.get("plant", ""),
            "sloc": di.get("storageLocation", "")
        } for di in delivery_items])
        print(f"  Delivery Items: {len(delivery_items)}")

        # 9. Billing Documents
        billing = read_jsonl("billing_document_headers")
        session.run("""
            UNWIND $batch AS b
            MERGE (n:BillingDocument {id: b.id})
            SET n.group = 'BillingDocument', n.label = 'Bill: ' + b.id,
                n.totalNetAmount = b.amt, n.currency = b.curr,
                n.creationDate = b.created, n.isCancelled = b.cancelled,
                n.companyCode = b.cc, n.accountingDocument = b.acctDoc,
                n.soldToParty = b.stp
        """, batch=[{
            "id": str(b.get("billingDocument")),
            "amt": b.get("totalNetAmount", ""),
            "curr": b.get("transactionCurrency", ""),
            "created": b.get("creationDate", ""),
            "cancelled": b.get("billingDocumentIsCancelled", False),
            "cc": b.get("companyCode", ""),
            "acctDoc": b.get("accountingDocument", ""),
            "stp": b.get("soldToParty", "")
        } for b in billing])
        print(f"  Billing Documents: {len(billing)}")

        # 10. Invoice Items
        billing_items = read_jsonl("billing_document_items")
        session.run("""
            UNWIND $batch AS bi
            MERGE (n:InvoiceItem {id: bi.iid_full})
            SET n.group = 'InvoiceItem', n.label = 'InvItem: ' + bi.iid,
                n.billingId = bi.bid, n.material = bi.mat, n.quantity = bi.qty,
                n.netAmount = bi.amt
        """, batch=[{
            "iid_full": f"{str(bi.get('billingDocument'))}-{normalize_item(str(bi.get('billingDocumentItem')))}",
            "bid": str(bi.get("billingDocument")),
            "iid": normalize_item(str(bi.get("billingDocumentItem"))),
            "mat": bi.get("material", ""),
            "qty": bi.get("billingQuantity", ""),
            "amt": bi.get("netAmount", "")
        } for bi in billing_items])
        print(f"  Invoice Items: {len(billing_items)}")

        # 11. Payments
        payments = read_jsonl("payments_accounts_receivable")
        session.run("""
            UNWIND $batch AS p
            MERGE (n:Payment {id: p.id})
            SET n.group = 'Payment', n.label = 'Pay: ' + p.id,
                n.amount = p.amt, n.currency = p.curr,
                n.clearingDate = p.cdate, n.customer = p.cust,
                n.clearingDoc = p.clearDoc
        """, batch=[{
            "id": str(p.get("accountingDocument")),
            "amt": p.get("amountInTransactionCurrency", ""),
            "curr": p.get("transactionCurrency", ""),
            "cdate": p.get("clearingDate", ""),
            "cust": p.get("customer", ""),
            "clearDoc": p.get("clearingAccountingDocument", "")
        } for p in payments])
        print(f"  Payments: {len(payments)}")

        # 12. Journal Entries
        journal_entries = read_jsonl("journal_entry_items_accounts_receivable")
        session.run("""
            UNWIND $batch AS je
            MERGE (n:JournalEntry {id: je.id})
            SET n.group = 'JournalEntry', n.label = 'JE: ' + je.id,
                n.amount = je.amt, n.docType = je.dtype,
                n.glAccount = je.gl, n.refDoc = je.ref
        """, batch=[{
            "id": str(je.get("accountingDocument")),
            "amt": je.get("amountInTransactionCurrency", ""),
            "dtype": je.get("accountingDocumentType", ""),
            "gl": je.get("glAccount", ""),
            "ref": je.get("referenceDocument", "")
        } for je in journal_entries])
        print(f"  Journal Entries: {len(journal_entries)}")

        # ========== PHASE 2: Create ALL Relationships (Batched) ==========
        print("\nPhase 2: Creating relationships...")

        # R1: Customer -[:PLACED]-> SalesOrder
        session.run("""
            UNWIND $batch AS r
            MATCH (c:Customer {id: r.cid}), (o:SalesOrder {id: r.oid})
            MERGE (c)-[:PLACED]->(o)
        """, batch=[{"cid": str(o.get("soldToParty", "")), "oid": str(o.get("salesOrder"))} for o in orders if o.get("soldToParty")])
        print("  R1: PLACED")

        # R2: Customer -[:HAS_ADDRESS]-> Address
        session.run("""
            UNWIND $batch AS r
            MATCH (c:Customer {id: r.cid}), (a:Address {id: r.aid})
            MERGE (c)-[:HAS_ADDRESS]->(a)
        """, batch=[{"cid": str(a.get("businessPartner")), "aid": str(a.get("addressId"))} for a in addresses if a.get("businessPartner")])
        print("  R2: HAS_ADDRESS")

        # R3: SalesOrder -[:HAS_ITEM]-> OrderItem
        session.run("""
            UNWIND $batch AS r
            MATCH (o:SalesOrder {id: r.oid}), (oi:OrderItem {id: r.oiid})
            MERGE (o)-[:HAS_ITEM]->(oi)
        """, batch=[{
            "oid": str(oi.get("salesOrder")),
            "oiid": f"{str(oi.get('salesOrder'))}-{normalize_item(str(oi.get('salesOrderItem')))}"
        } for oi in order_items])
        print("  R3: HAS_ITEM (Order)")

        # R4: OrderItem -[:OF_MATERIAL]-> Product
        session.run("""
            UNWIND $batch AS r
            MATCH (oi:OrderItem {id: r.oiid}), (p:Product {id: r.mat})
            MERGE (oi)-[:OF_MATERIAL]->(p)
        """, batch=[{
            "oiid": f"{str(oi.get('salesOrder'))}-{normalize_item(str(oi.get('salesOrderItem')))}",
            "mat": str(oi.get("material"))
        } for oi in order_items if oi.get("material")])
        print("  R4: OF_MATERIAL")

        # R5: Product -[:STORED_AT]-> Plant (batched in chunks of 100)
        product_plants = read_jsonl("product_plants")
        chunk_size = 100
        for i in range(0, len(product_plants), chunk_size):
            chunk = product_plants[i:i+chunk_size]
            session.run("""
                UNWIND $batch AS r
                MATCH (pr:Product {id: r.prod}), (pl:Plant {id: r.plant})
                MERGE (pr)-[:STORED_AT]->(pl)
            """, batch=[{"prod": str(pp.get("product")), "plant": str(pp.get("plant"))} for pp in chunk])
        print(f"  R5: STORED_AT ({len(product_plants)} mappings)")

        # R6: SalesOrder -[:DELIVERED_AS]-> Delivery
        session.run("""
            UNWIND $batch AS r
            MATCH (o:SalesOrder {id: r.so}), (d:Delivery {id: r.did})
            MERGE (o)-[:DELIVERED_AS]->(d)
        """, batch=[{
            "so": str(di.get("referenceSdDocument")),
            "did": str(di.get("deliveryDocument"))
        } for di in delivery_items if di.get("referenceSdDocument")])
        print("  R6: DELIVERED_AS")

        # R7: Customer -[:RECEIVED]-> Delivery
        session.run("""
            UNWIND $batch AS r
            MATCH (o:SalesOrder {id: r.so})<-[:PLACED]-(c:Customer), (d:Delivery {id: r.did})
            MERGE (c)-[:RECEIVED]->(d)
        """, batch=[{
            "so": str(di.get("referenceSdDocument")),
            "did": str(di.get("deliveryDocument"))
        } for di in delivery_items if di.get("referenceSdDocument")])
        print("  R7: RECEIVED")

        # R8: Delivery -[:CONTAINS_ITEM]-> DeliveryItem
        session.run("""
            UNWIND $batch AS r
            MATCH (d:Delivery {id: r.did}), (di:DeliveryItem {id: r.diid})
            MERGE (d)-[:CONTAINS_ITEM]->(di)
        """, batch=[{
            "did": str(di.get("deliveryDocument")),
            "diid": f"{str(di.get('deliveryDocument'))}-{normalize_item(str(di.get('deliveryDocumentItem')))}"
        } for di in delivery_items])
        print("  R8: CONTAINS_ITEM")

        # R9: DeliveryItem -[:SHIPPED_FROM]-> Plant
        session.run("""
            UNWIND $batch AS r
            MATCH (di:DeliveryItem {id: r.diid}), (p:Plant {id: r.plant})
            MERGE (di)-[:SHIPPED_FROM]->(p)
        """, batch=[{
            "diid": f"{str(di.get('deliveryDocument'))}-{normalize_item(str(di.get('deliveryDocumentItem')))}",
            "plant": str(di.get("plant"))
        } for di in delivery_items if di.get("plant")])
        print("  R9: SHIPPED_FROM")

        # R10: OrderItem -[:FULFILLED_BY]-> DeliveryItem
        session.run("""
            UNWIND $batch AS r
            MATCH (oi:OrderItem {id: r.oiid}), (di:DeliveryItem {id: r.diid})
            MERGE (oi)-[:FULFILLED_BY]->(di)
        """, batch=[{
            "oiid": f"{str(di.get('referenceSdDocument'))}-{normalize_item(str(di.get('referenceSdDocumentItem')))}",
            "diid": f"{str(di.get('deliveryDocument'))}-{normalize_item(str(di.get('deliveryDocumentItem')))}"
        } for di in delivery_items if di.get("referenceSdDocument") and di.get("referenceSdDocumentItem")])
        print("  R10: FULFILLED_BY")

        # R11: BillingDocument -[:HAS_ITEM]-> InvoiceItem
        session.run("""
            UNWIND $batch AS r
            MATCH (b:BillingDocument {id: r.bid}), (ii:InvoiceItem {id: r.iiid})
            MERGE (b)-[:HAS_ITEM]->(ii)
        """, batch=[{
            "bid": str(bi.get("billingDocument")),
            "iiid": f"{str(bi.get('billingDocument'))}-{normalize_item(str(bi.get('billingDocumentItem')))}"
        } for bi in billing_items])
        print("  R11: HAS_ITEM (Billing)")

        # R12: Delivery -[:BILLED_AS]-> BillingDocument
        session.run("""
            UNWIND $batch AS r
            MATCH (d:Delivery {id: r.deliv}), (b:BillingDocument {id: r.bid})
            MERGE (d)-[:BILLED_AS]->(b)
        """, batch=[{
            "deliv": str(bi.get("referenceSdDocument")),
            "bid": str(bi.get("billingDocument"))
        } for bi in billing_items if bi.get("referenceSdDocument")])
        print("  R12: BILLED_AS")

        # R13: DeliveryItem -[:BILLED_FROM]-> InvoiceItem
        session.run("""
            UNWIND $batch AS r
            MATCH (di:DeliveryItem {id: r.diid}), (ii:InvoiceItem {id: r.iiid})
            MERGE (di)-[:BILLED_FROM]->(ii)
        """, batch=[{
            "diid": f"{str(bi.get('referenceSdDocument'))}-{normalize_item(str(bi.get('referenceSdDocumentItem')))}",
            "iiid": f"{str(bi.get('billingDocument'))}-{normalize_item(str(bi.get('billingDocumentItem')))}"
        } for bi in billing_items if bi.get("referenceSdDocument") and bi.get("referenceSdDocumentItem")])
        print("  R13: BILLED_FROM")

        # R14: BillingDocument -[:GENERATES]-> JournalEntry
        session.run("""
            UNWIND $batch AS r
            MATCH (b:BillingDocument {id: r.ref}), (j:JournalEntry {id: r.jid})
            MERGE (b)-[:GENERATES]->(j)
        """, batch=[{
            "ref": str(je.get("referenceDocument")),
            "jid": str(je.get("accountingDocument"))
        } for je in journal_entries if je.get("referenceDocument")])
        print("  R14: GENERATES")

        # R15: JournalEntry -[:POSTED_TO]-> Customer
        session.run("""
            UNWIND $batch AS r
            MATCH (j:JournalEntry {id: r.jid}), (c:Customer {id: r.cust})
            MERGE (j)-[:POSTED_TO]->(c)
        """, batch=[{
            "jid": str(je.get("accountingDocument")),
            "cust": str(je.get("customer"))
        } for je in journal_entries if je.get("customer")])
        print("  R15: POSTED_TO")

        # R16: BillingDocument -[:PAID_BY]-> Payment
        # Link via accountingDocument: billing.accountingDocument == payment.clearingAccountingDocument
        acct_to_billing = {}
        for b in billing:
            acct = str(b.get("accountingDocument", ""))
            if acct:
                acct_to_billing[acct] = str(b.get("billingDocument"))

        paid_links = []
        for p in payments:
            pid = str(p.get("accountingDocument"))
            clearing = str(p.get("clearingAccountingDocument", ""))
            if clearing in acct_to_billing:
                paid_links.append({"bid": acct_to_billing[clearing], "pid": pid})
            elif pid in acct_to_billing:
                paid_links.append({"bid": acct_to_billing[pid], "pid": pid})

        if paid_links:
            session.run("""
                UNWIND $batch AS r
                MATCH (b:BillingDocument {id: r.bid}), (p:Payment {id: r.pid})
                MERGE (b)-[:PAID_BY]->(p)
            """, batch=paid_links)
        print(f"  R16: PAID_BY ({len(paid_links)} links)")

        # R17: Mark cancellations
        cancellations = read_jsonl("billing_document_cancellations")
        cancel_batch = [{"bid": str(cx.get("billingDocument"))} for cx in cancellations if cx.get("billingDocumentIsCancelled", False)]
        if cancel_batch:
            session.run("""
                UNWIND $batch AS r
                MERGE (b:BillingDocument {id: r.bid})
                SET b.status = 'CANCELLED', b.isCancelled = true
            """, batch=cancel_batch)
        print(f"  R17: Cancellations ({len(cancel_batch)})")

        print("\n✅ Graph construction complete!")

if __name__ == "__main__":
    ingest_data()
