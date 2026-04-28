import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "data/smartinvoice.db"

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_date TEXT NOT NULL,
            source TEXT DEFAULT 'image',
            vendor_name TEXT,
            invoice_number TEXT,
            date TEXT,
            total_amount REAL,
            tax_amount REAL,
            currency TEXT DEFAULT 'PKR',
            category TEXT,
            payment_method TEXT,
            items TEXT,
            raw_text TEXT,
            is_duplicate INTEGER DEFAULT 0,
            is_fraud INTEGER DEFAULT 0,
            fraud_flags TEXT,
            file_name TEXT,
            ai_summary TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            currency TEXT DEFAULT 'PKR',
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_invoice(data: dict) -> int:
    """Save an extracted invoice to the database. Returns the new row ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO invoices
        (upload_date, source, vendor_name, invoice_number, date, total_amount,
         tax_amount, currency, category, payment_method, items, raw_text,
         is_duplicate, is_fraud, fraud_flags, file_name, ai_summary)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("source", "image"),
        data.get("vendor_name"),
        data.get("invoice_number"),
        data.get("date"),
        data.get("total_amount"),
        data.get("tax_amount"),
        data.get("currency", "PKR"),
        data.get("category"),
        data.get("payment_method"),
        json.dumps(data.get("items", [])),
        data.get("raw_text", "")[:2000],
        1 if data.get("is_duplicate") else 0,
        1 if data.get("is_fraud") else 0,
        json.dumps(data.get("fraud_flags", [])),
        data.get("file_name", ""),
        data.get("ai_summary", "")
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_all_invoices() -> list:
    """Fetch all invoices from the database as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM invoices ORDER BY upload_date DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def delete_invoice(invoice_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
    conn.commit()
    conn.close()

def get_summary_stats() -> dict:
    """Return aggregate stats for the dashboard."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(total_amount), SUM(tax_amount) FROM invoices WHERE is_fraud=0")
    row = c.fetchone()
    total_count = row[0] or 0
    total_spend = row[1] or 0.0
    total_tax = row[2] or 0.0

    c.execute("SELECT COUNT(*) FROM invoices WHERE is_duplicate=1")
    duplicates = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM invoices WHERE is_fraud=1")
    frauds = c.fetchone()[0] or 0

    c.execute("""
        SELECT category, SUM(total_amount) as cat_total
        FROM invoices WHERE is_fraud=0 AND category IS NOT NULL
        GROUP BY category ORDER BY cat_total DESC
    """)
    by_category = {r[0]: r[1] for r in c.fetchall()}

    c.execute("""
        SELECT vendor_name, COUNT(*) as cnt, SUM(total_amount) as vtotal
        FROM invoices WHERE vendor_name IS NOT NULL
        GROUP BY vendor_name ORDER BY vtotal DESC LIMIT 5
    """)
    top_vendors = [{"vendor": r[0], "count": r[1], "total": r[2]} for r in c.fetchall()]

    c.execute("""
        SELECT strftime('%Y-%m', upload_date) as month, SUM(total_amount)
        FROM invoices WHERE is_fraud=0
        GROUP BY month ORDER BY month
    """)
    monthly = {r[0]: r[1] for r in c.fetchall()}

    conn.close()
    return {
        "total_count": total_count,
        "total_spend": total_spend,
        "total_tax": total_tax,
        "duplicates": duplicates,
        "frauds": frauds,
        "by_category": by_category,
        "top_vendors": top_vendors,
        "monthly": monthly,
    }

def save_budget(category: str, limit: float, currency: str = "PKR"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM budgets WHERE category=?", (category,))
    c.execute("INSERT INTO budgets (category, monthly_limit, currency, created_at) VALUES (?,?,?,?)",
              (category, limit, currency, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_budgets() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM budgets")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
