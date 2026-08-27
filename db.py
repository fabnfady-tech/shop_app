"""
طبقة قاعدة البيانات - SQLite محلي بالكامل
"""
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

PRODUCT_CATEGORIES = ["طعام", "إكسسوارات", "أدوية وعناية", "ألعاب", "نظافة",'حيوانات', 'زواحف','طيور','اسماك', "أخرى"]
EXPENSE_CATEGORIES = ["إيجار", "رواتب", "فواتير (كهرباء / مياه / نت)", "شراء بضاعة",
                       "صيانة", "سلف", "إهلاك", "أخرى"]
UNITS = ["قطعة", "كيلو"]


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock REAL NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'أخرى',
                unit TEXT NOT NULL DEFAULT 'قطعة'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL,
                payment_type TEXT NOT NULL DEFAULT 'نقدي',
                customer_id INTEGER,
                paid INTEGER NOT NULL DEFAULT 1,
                paid_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL DEFAULT 'قطعة',
                unit_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                refund_amount REAL NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            )
        """)


def invoice_serial(sale_id):
    return f"INV-{sale_id:05d}"


# ---------------- Products ----------------
def add_product(name, price, stock, category, unit):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO products (name, price, stock, category, unit) VALUES (?, ?, ?, ?, ?)",
            (name, price, stock, category, unit),
        )


def update_product(product_id, name, price, stock, category, unit):
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET name=?, price=?, stock=?, category=?, unit=? WHERE id=?",
            (name, price, stock, category, unit, product_id),
        )


def delete_product(product_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))


def get_products(search="", category=None):
    with get_connection() as conn:
        query = "SELECT * FROM products WHERE name LIKE ?"
        params = [f"%{search}%"]
        if category and category != "الكل":
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY name"
        return conn.execute(query, params).fetchall()


def get_category_counts():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS c FROM products GROUP BY category ORDER BY category"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        result = [("الكل", total)]
        result += [(r["category"], r["c"]) for r in rows]
        return result


def adjust_stock(product_id, delta):
    with get_connection() as conn:
        conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (delta, product_id))


# ---------------- Customers ----------------
def get_or_create_customer(name, phone):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM customers WHERE name=? AND phone=?", (name, phone)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
        return cur.lastrowid


# ---------------- Sales ----------------
def create_sale(cart_items, discount, payment_type, customer_name=None, customer_phone=None):
    """cart_items: list of {product_id, product_name, quantity, unit, unit_price}"""
    subtotal = sum(item["quantity"] * item["unit_price"] for item in cart_items)
    discount = min(discount, subtotal)
    total = subtotal - discount
    customer_id = None
    if payment_type == "آجل" and customer_name and customer_phone:
        customer_id = get_or_create_customer(customer_name, customer_phone)
    paid = 1 if payment_type == "نقدي" else 0
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO sales (subtotal, discount, total, payment_type, customer_id, paid, paid_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (subtotal, discount, total, payment_type, customer_id, paid,
             now if paid else None, now),
        )
        sale_id = cur.lastrowid
        for item in cart_items:
            conn.execute(
                """INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit, unit_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sale_id, item["product_id"], item["product_name"], item["quantity"],
                 item["unit"], item["unit_price"]),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
    return sale_id, total


def get_sale_items(sale_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)
        ).fetchall()


def get_sales_for_date(target_date):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sales WHERE date(created_at) = ? ORDER BY created_at DESC",
            (target_date,),
        ).fetchall()


def get_sales_for_month(year, month):
    prefix = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sales WHERE substr(created_at, 1, 7) = ? ORDER BY created_at DESC",
            (prefix,),
        ).fetchall()
def search_sales(query):
    """بيدور بتاريخ (YYYY-MM-DD) أو برقم فاتورة/سيريال (زي INV-00007 أو 7 أو 00007)."""
    import re
    query = (query or "").strip()
    if not query:
        return []
    if re.match(r"^\d{4}-\d{2}-\d{2}$", query):
        return get_sales_for_date(query)
    q = query.upper().replace(" ", "")
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM sales ORDER BY created_at DESC").fetchall()
    return [r for r in rows if q in invoice_serial(r["id"])]

def get_deferred_sales(only_unpaid=True):
    with get_connection() as conn:
        query = """
            SELECT sales.*, customers.name AS customer_name, customers.phone AS customer_phone
            FROM sales LEFT JOIN customers ON sales.customer_id = customers.id
            WHERE sales.payment_type = 'آجل'
        """
        if only_unpaid:
            query += " AND sales.paid = 0"
        query += " ORDER BY sales.created_at DESC"
        return conn.execute(query).fetchall()


def mark_sale_paid(sale_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE sales SET paid = 1, paid_at = ? WHERE id = ?",
            (datetime.now().isoformat(timespec="seconds"), sale_id),
        )


# ---------------- Returns ----------------
def add_return(product_id, product_name, quantity, refund_amount, reason):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO returns (product_id, product_name, quantity, refund_amount, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (product_id, product_name, quantity, refund_amount, reason,
             datetime.now().isoformat(timespec="seconds")),
        )
        if product_id:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product_id))


def get_returns(limit=50):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM returns ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


def get_returns_total_for_date(target_date):
    with get_connection() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(refund_amount),0) AS t FROM returns WHERE date(created_at) = ?",
            (target_date,),
        ).fetchone()["t"]


# ---------------- Expenses ----------------
def add_expense(description, category, amount, is_recurring=False):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (description, category, amount, is_recurring, created_at) VALUES (?, ?, ?, ?, ?)",
            (description, category, amount, 1 if is_recurring else 0,
             datetime.now().isoformat(timespec="seconds")),
        )


def delete_expense(expense_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))


def get_expenses_for_date(target_date):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM expenses WHERE date(created_at) = ? ORDER BY created_at DESC",
            (target_date,),
        ).fetchall()


def apply_recurring_expenses():
    """بتتأكد إن كل مصروف متكرر (زي الإهلاك) اتسجل مرة في الشهر الحالي، ولو لأ بتسجله تلقائي."""
    today = date.today()
    month_prefix = f"{today.year:04d}-{today.month:02d}"
    with get_connection() as conn:
        templates = conn.execute(
            "SELECT DISTINCT description, category, amount FROM expenses WHERE is_recurring = 1"
        ).fetchall()
        for t in templates:
            exists = conn.execute(
                """SELECT id FROM expenses WHERE description=? AND category=? AND is_recurring=1
                   AND substr(created_at,1,7)=?""",
                (t["description"], t["category"], month_prefix),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO expenses (description, category, amount, is_recurring, created_at) VALUES (?, ?, ?, 1, ?)",
                    (t["description"], t["category"], t["amount"], today.isoformat()),
                )


# ---------------- Reports ----------------
def get_daily_report(target_date=None):
    if target_date is None:
        target_date = date.today().isoformat()
    with get_connection() as conn:
        cash_income = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE date(created_at)=? AND payment_type='نقدي'",
            (target_date,),
        ).fetchone()["t"]
        deferred_collected = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE date(paid_at)=? AND payment_type='آجل'",
            (target_date,),
        ).fetchone()["t"]
        deferred_new = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE date(created_at)=? AND payment_type='آجل'",
            (target_date,),
        ).fetchone()["t"]
        deferred_outstanding = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE payment_type='آجل' AND paid=0"
        ).fetchone()["t"]
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE date(created_at)=?",
            (target_date,),
        ).fetchone()["t"]
        returns_total = get_returns_total_for_date(target_date)
        num_sales = conn.execute(
            "SELECT COUNT(*) AS c FROM sales WHERE date(created_at)=?", (target_date,)
        ).fetchone()["c"]
        low_stock = conn.execute("SELECT * FROM products WHERE stock <= 3 ORDER BY stock ASC").fetchall()

    cash_income_total = cash_income + deferred_collected
    net = cash_income_total - expenses - returns_total
    return {
        "date": target_date,
        "cash_income": cash_income,
        "deferred_collected": deferred_collected,
        "cash_income_total": cash_income_total,
        "deferred_new": deferred_new,
        "deferred_outstanding": deferred_outstanding,
        "expenses": expenses,
        "returns_total": returns_total,
        "net": net,
        "num_sales": num_sales,
        "low_stock": low_stock,
    }
