import os
import json
import sqlite3
import glob

DB_NAME = "sap_o2c.db"
DATA_DIR = "../sap-o2c-data"

def init_db(conn):
    c = conn.cursor()
    
    # 1. Customers
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            businessPartner TEXT PRIMARY KEY,
            businessPartnerName TEXT,
            cityName TEXT,
            country TEXT
        )
    """)
    
    # 2. Products
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product TEXT PRIMARY KEY,
            productDescription TEXT,
            productGroup TEXT
        )
    """)

    # 3. Plants
    c.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            plant TEXT PRIMARY KEY,
            plantName TEXT
        )
    """)

    # 4. Sales Orders
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales_orders (
            salesOrder TEXT PRIMARY KEY,
            soldToParty TEXT,
            totalNetAmount REAL,
            transactionCurrency TEXT,
            pricingDate TEXT,
            overallDeliveryStatus TEXT
        )
    """)

    # 5. Sales Order Items
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales_order_items (
            salesOrder TEXT,
            salesOrderItem TEXT,
            material TEXT,
            requestedQuantity REAL,
            netAmount REAL,
            productionPlant TEXT,
            storageLocation TEXT,
            PRIMARY KEY(salesOrder, salesOrderItem)
        )
    """)

    # 6. Deliveries
    c.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            deliveryDocument TEXT PRIMARY KEY,
            creationDate TEXT,
            overallGoodsMovementStatus TEXT,
            shippingPoint TEXT
        )
    """)

    # 7. Delivery Items
    c.execute("""
        CREATE TABLE IF NOT EXISTS delivery_items (
            deliveryDocument TEXT,
            deliveryDocumentItem TEXT,
            actualDeliveryQuantity REAL,
            plant TEXT,
            referenceSdDocument TEXT,
            referenceSdDocumentItem TEXT,
            PRIMARY KEY(deliveryDocument, deliveryDocumentItem)
        )
    """)

    # 8. Billing Documents
    c.execute("""
        CREATE TABLE IF NOT EXISTS billing_documents (
            billingDocument TEXT PRIMARY KEY,
            billingDocumentType TEXT,
            billingDocumentDate TEXT,
            totalNetAmount REAL,
            transactionCurrency TEXT,
            payerParty TEXT,
            accountingDocument TEXT
        )
    """)
    
    # 9. Billing Document Items
    c.execute("""
        CREATE TABLE IF NOT EXISTS billing_document_items (
            billingDocument TEXT,
            billingDocumentItem TEXT,
            salesDocument TEXT,
            salesDocumentItem TEXT,
            referenceSdDocument TEXT,
            referenceSdDocumentItem TEXT,
            material TEXT,
            billingQuantity REAL,
            netAmount REAL,
            PRIMARY KEY(billingDocument, billingDocumentItem)
        )
    """)

    # 10. Journal Entries
    c.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            accountingDocument TEXT,
            referenceDocument TEXT,
            customer TEXT,
            amountInTransactionCurrency REAL,
            postingDate TEXT
        )
    """)

    # 11. Payments
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            accountingDocument TEXT,
            clearingAccountingDocument TEXT,
            amountInTransactionCurrency REAL,
            customer TEXT,
            invoiceReference TEXT,
            clearingDate TEXT
        )
    """)

    conn.commit()


def load_jsonl(conn, subdir_name, table_name, extract_func):
    path_pattern = os.path.join(DATA_DIR, subdir_name, "*.jsonl")
    files = glob.glob(path_pattern)
    c = conn.cursor()
    count = 0
    row_cache = []
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                row = extract_func(data)
                if row:
                    row_cache.append(row)
                    count += 1
                    
                if len(row_cache) >= 5000:
                    placeholders = ",".join(["?"] * len(row_cache[0]))
                    c.executemany(f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})", row_cache)
                    row_cache = []

    if row_cache:
        placeholders = ",".join(["?"] * len(row_cache[0]))
        c.executemany(f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})", row_cache)
    
    conn.commit()
    print(f"Loaded {count} records into {table_name} from {subdir_name}")


def main():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)

    # 1. Customers mapping (business_partners + addresses)
    # We will do a 2-pass over BP and Address, but since data is small, let's load BP to memory
    bp_dict = {}
    path_pattern = os.path.join(DATA_DIR, "business_partners", "*.jsonl")
    for file in glob.glob(path_pattern):
        with open(file, 'r') as f:
            for line in f:
                d = json.loads(line)
                bp_dict[d.get("businessPartner")] = {
                    "name": d.get("businessPartnerName"), "city": "", "country": ""
                }
    
    path_pattern = os.path.join(DATA_DIR, "business_partner_addresses", "*.jsonl")
    for file in glob.glob(path_pattern):
        with open(file, 'r') as f:
            for line in f:
                d = json.loads(line)
                bp = d.get("businessPartner")
                if bp in bp_dict:
                    bp_dict[bp]["city"] = d.get("cityName")
                    bp_dict[bp]["country"] = d.get("country")
                    
    c = conn.cursor()
    for bp, info in bp_dict.items():
        c.execute("INSERT OR IGNORE INTO customers (businessPartner, businessPartnerName, cityName, country) VALUES (?, ?, ?, ?)",
                  (bp, info["name"], info["city"], info["country"]))
    conn.commit()
    print(f"Loaded {len(bp_dict)} records into customers")

    # 2. Products -> load products and merge descriptions
    prod_dict = {}
    for file in glob.glob(os.path.join(DATA_DIR, "products", "*.jsonl")):
        with open(file, 'r') as f:
            for line in f:
                d = json.loads(line)
                prod_dict[d.get("product")] = {"group": d.get("productGroup"), "desc": ""}
    for file in glob.glob(os.path.join(DATA_DIR, "product_descriptions", "*.jsonl")):
        with open(file, 'r') as f:
            for line in f:
                d = json.loads(line)
                if d.get("language") == "EN":
                    p = d.get("product")
                    if p in prod_dict:
                        prod_dict[p]["desc"] = d.get("productDescription")
    
    for p, info in prod_dict.items():
        c.execute("INSERT OR IGNORE INTO products VALUES (?, ?, ?)", (p, info["desc"], info["group"]))
    conn.commit()
    print(f"Loaded {len(prod_dict)} records into products")

    # Load the straightforward tables
    load_jsonl(conn, "plants", "plants", lambda d: (d.get("plant"), d.get("plantName")))
    
    load_jsonl(conn, "sales_order_headers", "sales_orders", lambda d: (
        d.get("salesOrder"), d.get("soldToParty"), float(d.get("totalNetAmount") or 0),
        d.get("transactionCurrency"), d.get("pricingDate"), d.get("overallDeliveryStatus")
    ))

    load_jsonl(conn, "sales_order_items", "sales_order_items", lambda d: (
        d.get("salesOrder"), d.get("salesOrderItem"), d.get("material"),
        float(d.get("requestedQuantity") or 0), float(d.get("netAmount") or 0),
        d.get("productionPlant"), d.get("storageLocation")
    ))

    load_jsonl(conn, "outbound_delivery_headers", "deliveries", lambda d: (
        d.get("deliveryDocument"), d.get("creationDate"), d.get("overallGoodsMovementStatus"), d.get("shippingPoint")
    ))

    load_jsonl(conn, "outbound_delivery_items", "delivery_items", lambda d: (
        d.get("deliveryDocument"), d.get("deliveryDocumentItem"), float(d.get("actualDeliveryQuantity") or 0),
        d.get("plant"), d.get("referenceSdDocument"), d.get("referenceSdDocumentItem")
    ))

    load_jsonl(conn, "billing_document_headers", "billing_documents", lambda d: (
        d.get("billingDocument"), d.get("billingDocumentType"), d.get("billingDocumentDate"),
        float(d.get("totalNetAmount") or 0), d.get("transactionCurrency"), d.get("payerParty"), d.get("accountingDocument")
    ))

    load_jsonl(conn, "billing_document_items", "billing_document_items", lambda d: (
        d.get("billingDocument"), d.get("billingDocumentItem"), d.get("salesDocument"), d.get("salesDocumentItem"),
        d.get("referenceSdDocument"), d.get("referenceSdDocumentItem"), d.get("material"),
        float(d.get("billingQuantity") or 0), float(d.get("netAmount") or 0)
    ))

    load_jsonl(conn, "journal_entry_items_accounts_receivable", "journal_entries", lambda d: (
        d.get("accountingDocument"), d.get("referenceDocument"), d.get("customer"),
        float(d.get("amountInTransactionCurrency") or 0), d.get("postingDate")
    ))

    load_jsonl(conn, "payments_accounts_receivable", "payments", lambda d: (
        d.get("accountingDocument"), d.get("clearingAccountingDocument"),
        float(d.get("amountInTransactionCurrency") or 0), d.get("customer"),
        d.get("invoiceReference"), d.get("clearingDate")
    ))
    
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
