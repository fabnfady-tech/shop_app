"""
طبقة قاعدة البيانات - SQLite محلي بالكامل
"""
import sqlite3
import hashlib
from datetime import datetime, date
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

PRODUCT_CATEGORIES = ["طعام", "إكسسوارات", "أدوية وعناية", "ألعاب", "نظافة", "حيوانات", "زواحف", "طيور", "اسماك", "أخرى"]
EXPENSE_CATEGORIES = ["إيجار", "رواتب", "فواتير (كهرباء / مياه / نت)", "شراء بضاعة", "صيانة", "سلف", "إهلاك", "أخرى"]
UNITS = ["قطعة", "كيلو"]

EPSILON = 1e-6


class ReturnValidationError(Exception):
    """تُثار عند تسجيل مرتجع غير منطقي."""
    pass


class PaymentValidationError(Exception):
    """تُثار عند تسجيل دفعة غير صحيحة."""
    pass


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


def _column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


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
                phone TEXT NOT NULL,
                address TEXT
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
                paid_amount REAL NOT NULL DEFAULT 0,
                delivery_status TEXT,
                delivery_address TEXT,
                delivery_fee REAL DEFAULT 0,
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sale_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ---- الترحيلات (Migrations) ----
      # ---- الترحيلات (Migrations) ----
        if not _column_exists(conn, "sales", "paid_amount"):
            conn.execute("ALTER TABLE sales ADD COLUMN paid_amount REAL NOT NULL DEFAULT 0")
            conn.execute("UPDATE sales SET paid_amount = total WHERE paid = 1")

        if not _column_exists(conn, "customers", "address"):
            conn.execute("ALTER TABLE customers ADD COLUMN address TEXT")

        if not _column_exists(conn, "sales", "delivery_status"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_status TEXT")

        if not _column_exists(conn, "sales", "delivery_address"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_address TEXT")

        if not _column_exists(conn, "sales", "delivery_fee"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_fee REAL DEFAULT 0")

        # أضف هذا السطر هنا لتفادي خطأ no such column: sales.is_delivery
        if not _column_exists(conn, "sales", "is_delivery"):
            conn.execute("ALTER TABLE sales ADD COLUMN is_delivery INTEGER DEFAULT 0")
        # ---- الترحيلات (Migrations) ----
        if not _column_exists(conn, "sales", "paid_amount"):
            conn.execute("ALTER TABLE sales ADD COLUMN paid_amount REAL NOT NULL DEFAULT 0")
            conn.execute("UPDATE sales SET paid_amount = total WHERE paid = 1")

        if not _column_exists(conn, "customers", "address"):
            conn.execute("ALTER TABLE customers ADD COLUMN address TEXT")

        if not _column_exists(conn, "sales", "delivery_status"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_status TEXT")

        if not _column_exists(conn, "sales", "delivery_address"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_address TEXT")

        if not _column_exists(conn, "sales", "delivery_fee"):
            conn.execute("ALTER TABLE sales ADD COLUMN delivery_fee REAL DEFAULT 0")

        if not _column_exists(conn, "sales", "is_delivery"):
            conn.execute("ALTER TABLE sales ADD COLUMN is_delivery INTEGER DEFAULT 0")
        if not _column_exists(conn, "sales", "customer_name"):
            conn.execute("ALTER TABLE sales ADD COLUMN customer_name TEXT")

        if not _column_exists(conn, "sales", "customer_phone"):
            conn.execute("ALTER TABLE sales ADD COLUMN customer_phone TEXT")
        # ضع السطر هنا لتحديث الطلبات القديمة وجعلها تظهر فوراً
        conn.execute("UPDATE sales SET is_delivery = 1 WHERE delivery_status IS NOT NULL OR delivery_fee > 0 OR delivery_address IS NOT NULL;")
        conn.commit()


def invoice_serial(sale_id):
    return f"INV-{sale_id:05d}"


def _hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


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


def get_product_sold_quantity(product_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) AS q FROM sale_items WHERE product_id=?",
            (product_id,),
        ).fetchone()
        return row["q"]


def get_product_returned_quantity(product_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) AS q FROM returns WHERE product_id=?",
            (product_id,),
        ).fetchone()
        return row["q"]


def get_product_returnable_quantity(product_id):
    sold = get_product_sold_quantity(product_id)
    returned = get_product_returned_quantity(product_id)
    remaining = sold - returned
    return remaining if remaining > 0 else 0


# ---------------- Customers ----------------
def get_or_create_customer(name, phone, address=None):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM customers WHERE phone=? OR name=?", (phone, name)
        ).fetchone()
        if row:
            if address:
                conn.execute("UPDATE customers SET address=? WHERE id=?", (address, row["id"]))
            return row["id"]
        cur = conn.execute(
            "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
            (name, phone, address)
        )
        return cur.lastrowid


def find_customer_by_any(search_val):
    """البحث عن العميل باستخدام رقم التليفون أو الاسم أو العنوان"""
    search_val = (search_val or "").strip()
    if not search_val or len(search_val) < 2:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """SELECT name, phone, address
               FROM customers
               WHERE phone LIKE ? OR name LIKE ? OR address LIKE ?
               ORDER BY id DESC LIMIT 1""",
            (f"%{search_val}%", f"%{search_val}%", f"%{search_val}%")
        ).fetchone()
        return dict(row) if row else None


def save_or_update_customer(name, phone, address=None):
    """حفظ عميل جديد أو تحديث بياناته إذا كان مقيداً"""
    if not phone or not name:
        return None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, address FROM customers WHERE phone = ?", (phone,)
        ).fetchone()

        if row:
            new_address = address if address else row["address"]
            conn.execute(
                "UPDATE customers SET name = ?, address = ? WHERE phone = ?",
                (name, new_address, phone)
            )
            return row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                (name, phone, address)
            )
            return cur.lastrowid


def search_customers(query):
    """البحث عن عدة عملاء بالاسم أو رقم الهاتف أو العنوان لعرضهم في القوائم أو الجداول"""
    query = (query or "").strip()
    with get_connection() as conn:
        if not query:
            return conn.execute("SELECT * FROM customers ORDER BY name").fetchall()

        return conn.execute(
            """SELECT * FROM customers
                WHERE name LIKE ? OR phone LIKE ? OR address LIKE ?
                ORDER BY name""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()


# ---------------- Sales ----------------
def create_sale(cart_items, discount, payment_type, customer_name=None, customer_phone=None,
                delivery_address=None, delivery_fee=0.0):
    subtotal = sum(item["quantity"] * item["unit_price"] for item in cart_items)
    discount = min(discount, subtotal)
    total = subtotal - discount + delivery_fee
    
    customer_id = None
    if customer_name or customer_phone:
        customer_id = get_or_create_customer(customer_name, customer_phone, delivery_address)

    is_delivery = 1 if (payment_type == "دليفري" or bool(delivery_address) or delivery_fee > 0 or bool(customer_phone)) else 0
    delivery_status = "قيد الانتظار" if is_delivery == 1 else None

    paid = 1 if payment_type != "آجل" else 0
    paid_amount = total if paid else 0.0
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO sales (subtotal, discount, total, payment_type, customer_id, customer_name, customer_phone, paid, paid_at, created_at, paid_amount, delivery_status, delivery_address, delivery_fee, is_delivery)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (subtotal, discount, total, payment_type, customer_id, customer_name, customer_phone, paid,
             now if paid else None, now, paid_amount, delivery_status, delivery_address, delivery_fee, is_delivery),
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
        if paid_amount > 0:
            conn.execute(
                "INSERT INTO sale_payments (sale_id, amount, created_at) VALUES (?, ?, ?)",
                (sale_id, paid_amount, now),
            )
    return sale_id, total


def delete_sale(sale_id):
    """
    حذف فاتورة بالكامل: بنودها ومدفوعاتها والفاتورة نفسها،
    مع إرجاع الكميات المباعة إلى المخزون تلقائيًا.
    """
    with get_connection() as conn:
        items = conn.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)).fetchall()
        for it in items:
            if it["product_id"]:
                conn.execute(
                    "UPDATE products SET stock = stock + ? WHERE id = ?",
                    (it["quantity"], it["product_id"]),
                )
        conn.execute("DELETE FROM sale_payments WHERE sale_id=?", (sale_id,))
        conn.execute("DELETE FROM sale_items WHERE sale_id=?", (sale_id,))
        conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))


def get_sale_items(sale_id):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()


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


def get_year_summary(year):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT CAST(substr(created_at, 6, 2) AS INTEGER) AS month,
                      COUNT(*) AS c, COALESCE(SUM(total), 0) AS t
               FROM sales
               WHERE substr(created_at, 1, 4) = ?
               GROUP BY month""",
            (f"{year:04d}",),
        ).fetchall()
        summary = {m: {"count": 0, "total": 0.0} for m in range(1, 13)}
        for r in rows:
            summary[r["month"]] = {"count": r["c"], "total": r["t"]}
        return summary


def search_sales(query):
    import re
    query = (query or "").strip()
    if not query:
        return []
    if re.match(r"^\d{4}-\d{2}-\d{2}$", query):
        return get_sales_for_date(query)

    q = query.upper().replace(" ", "")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sales.*, customers.name AS customer_name, customers.phone AS customer_phone
            FROM sales
            LEFT JOIN customers ON sales.customer_id = customers.id
            ORDER BY sales.created_at DESC
        """).fetchall()

    results = []
    for r in rows:
        serial = invoice_serial(r["id"]).upper()
        cust_name = (r["customer_name"] or "").upper()
        cust_phone = (r["customer_phone"] or "").upper()
        if q in serial or q in cust_name or q in cust_phone:
            results.append(r)
    return results


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


def get_sale_payments(sale_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sale_payments WHERE sale_id = ? ORDER BY created_at DESC", (sale_id,)
        ).fetchall()


def add_payment(sale_id, amount):
    if amount is None or amount <= 0:
        raise PaymentValidationError("لازم تدخل مبلغ أكبر من صفر")
    with get_connection() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if not sale:
            raise PaymentValidationError("الفاتورة دي مش موجودة")
        remaining = sale["total"] - sale["paid_amount"]
        if amount > remaining + EPSILON:
            raise PaymentValidationError(
                f"المبلغ أكبر من المتبقي على العميل ({remaining:.2f} ج.م بس)"
            )
        now = datetime.now().isoformat(timespec="seconds")
        new_paid_amount = min(sale["paid_amount"] + amount, sale["total"])
        fully_paid = 1 if (sale["total"] - new_paid_amount) <= EPSILON else 0
        conn.execute(
            "INSERT INTO sale_payments (sale_id, amount, created_at) VALUES (?, ?, ?)",
            (sale_id, amount, now),
        )
        conn.execute(
            "UPDATE sales SET paid_amount=?, paid=?, paid_at=? WHERE id=?",
            (new_paid_amount, fully_paid, now if fully_paid else sale["paid_at"], sale_id),
        )
        new_remaining = sale["total"] - new_paid_amount
        return new_paid_amount, new_remaining, bool(fully_paid)


def mark_sale_paid(sale_id):
    with get_connection() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if not sale:
        return
    remaining = sale["total"] - sale["paid_amount"]
    if remaining > EPSILON:
        add_payment(sale_id, remaining)


def add_deferred_payment(sales_id, amount_paid):
    return add_payment(sales_id, amount_paid)


# ---------------- Returns ----------------
def add_return(product_id, product_name, quantity, refund_amount, reason):
    if quantity is None or quantity <= 0:
        raise ReturnValidationError("لازم تكتب كمية أكبر من صفر")

    if product_id:
        returnable = get_product_returnable_quantity(product_id)
        if quantity > returnable + EPSILON:
            sold = get_product_sold_quantity(product_id)
            already_returned = get_product_returned_quantity(product_id)
            if returnable <= 0:
                raise ReturnValidationError(
                    f'المرتجع ده مش موجود أصلاً - "{product_name}" مباعش منه كمية كافية لسه '
                    f'(اتباع {sold:g} واترجع منه {already_returned:g} قبل كده)'
                )
            raise ReturnValidationError(
                f'الكمية أكبر من المتاح للإرجاع - أقصى كمية ممكن ترجعها من "{product_name}" '
                f'هي {returnable:g} بس (اتباع {sold:g} واترجع منه {already_returned:g} قبل كده)'
            )

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
    today = date.today()
    month_prefix = f"{today.year:04d}-{today.month:02d}"
    now_iso = datetime.now().isoformat(timespec="seconds")
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
                    (t["description"], t["category"], t["amount"], now_iso),
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
        wallet_income = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE date(created_at)=? AND payment_type='محفظة'",
            (target_date,),
        ).fetchone()["t"]
        deferred_collected = conn.execute(
            """SELECT COALESCE(SUM(sp.amount),0) AS t FROM sale_payments sp
               JOIN sales s ON s.id = sp.sale_id
               WHERE date(sp.created_at)=? AND s.payment_type='آجل'""",
            (target_date,),
        ).fetchone()["t"]
        deferred_new = conn.execute(
            "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE date(created_at)=? AND payment_type='آجل'",
            (target_date,),
        ).fetchone()["t"]
        deferred_outstanding = conn.execute(
            "SELECT COALESCE(SUM(total - paid_amount),0) AS t FROM sales WHERE payment_type='آجل' AND paid=0"
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

    cash_income_total = cash_income + wallet_income + deferred_collected
    net = cash_income_total - expenses - returns_total
    return {
        "date": target_date,
        "cash_income": cash_income,
        "wallet_income": wallet_income,
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


# ---------------- Admin / Settings ----------------
def get_setting(key, default=None):
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def is_admin_password_set():
    return get_setting("admin_password_hash") is not None


def set_admin_password(password, security_question, security_answer):
    set_setting("admin_password_hash", _hash(password))
    set_setting("security_question", security_question)
    set_setting("security_answer_hash", _hash(security_answer.strip().lower()))


def verify_admin_password(password):
    stored = get_setting("admin_password_hash")
    return stored is not None and stored == _hash(password)


def get_security_question():
    return get_setting("security_question")


def verify_security_answer(answer):
    stored = get_setting("security_answer_hash")
    return stored is not None and stored == _hash((answer or "").strip().lower())


def reset_admin_password(new_password):
    set_setting("admin_password_hash", _hash(new_password))


# ---------------- Delivery Management ----------------
def get_delivery_orders(status_filter="الكل"):
    """جلب كل طلبات الدليفري من جدول sales"""
    with get_connection() as conn:
        query = """
            SELECT
                sales.id,
                customers.name AS customer_name,
                customers.phone AS customer_phone,
                sales.total AS total_amount,
                sales.payment_type,
                COALESCE(sales.delivery_status, 'قيد الانتظار') AS delivery_status,
                COALESCE(sales.delivery_address, customers.address, 'لم يحدد') AS delivery_address,
                COALESCE(sales.delivery_fee, 0.0) AS delivery_fee,
                sales.created_at
            FROM sales
            LEFT JOIN customers ON sales.customer_id = customers.id
            WHERE sales.payment_type = 'دليفري' OR sales.delivery_status IS NOT NULL
        """
        params = []
        if status_filter != "الكل":
            query += " AND COALESCE(sales.delivery_status, 'قيد الانتظار') = ?"
            params.append(status_filter)
        query += " ORDER BY sales.id DESC"

        rows = conn.execute(query, params).fetchall()
        orders = []
        for r in rows:
            orders.append({
                "id": r["id"],
                "customer_name": r["customer_name"] or "عميل عام",
                "customer_phone": r["customer_phone"] or "لا يوجد",
                "total_amount": r["total_amount"] or 0.0,
                "payment_type": r["payment_type"] or "نقدي",
                "delivery_status": r["delivery_status"] or "قيد الانتظار",
                "status": r["delivery_status"] or "قيد الانتظار",
                "address": r["delivery_address"] or "لم يحدد",
                "delivery_address": r["delivery_address"] or "لم يحدد",
                "delivery_fee": r["delivery_fee"] or 0.0,
                "created_at": r["created_at"] or "",
            })
        return orders


def get_delivery_orders_by_phone(phone=""):
    phone = (phone or "").strip()
    with get_connection() as conn:
        query = """
            SELECT 
                sales.id,
                sales.customer_id,
                sales.customer_name AS s_name,
                sales.customer_phone AS s_phone,
                customers.name AS c_name,
                customers.phone AS c_phone,
                customers.address AS c_address,
                sales.total AS total_amount,
                sales.payment_type,
                COALESCE(sales.delivery_status, 'قيد الانتظار') AS delivery_status,
                COALESCE(sales.delivery_address, customers.address, 'لم يحدد') AS delivery_address,
                COALESCE(sales.delivery_fee, 0.0) AS delivery_fee,
                sales.created_at
            FROM sales
            LEFT JOIN customers ON sales.customer_id = customers.id
            WHERE sales.is_delivery = 1 OR sales.delivery_status IS NOT NULL
        """
        params = []
        if phone:
            query += " AND (sales.customer_phone LIKE ? OR customers.phone LIKE ?)"
            params.extend([f"%{phone}%", f"%{phone}%"])
            
        query += " ORDER BY sales.id DESC"

        rows = conn.execute(query, params).fetchall()

        orders = []
        for r in rows:
            keys = r.keys()
            
            # ترتيب الأولوية: 1. جدول العملاء المرتبط (c_name)، 2. الاسم المحفوظ مباشرة (s_name)
            c_name = None
            if "c_name" in keys and r["c_name"]:
                c_name = r["c_name"]
            elif "s_name" in keys and r["s_name"]:
                c_name = r["s_name"]

            c_phone = None
            if "c_phone" in keys and r["c_phone"]:
                c_phone = r["c_phone"]
            elif "s_phone" in keys and r["s_phone"]:
                c_phone = r["s_phone"]

            orders.append({
                "id": r["id"],
                "customer_name": c_name or "عميل عام",
                "customer_phone": c_phone or "لا يوجد",
                "total_amount": r["total_amount"] if "total_amount" in keys and r["total_amount"] else 0.0,
                "payment_type": r["payment_type"] if "payment_type" in keys and r["payment_type"] else "نقدي",
                "delivery_status": r["delivery_status"] if "delivery_status" in keys and r["delivery_status"] else "قيد الانتظار",
                "status": r["delivery_status"] if "delivery_status" in keys and r["delivery_status"] else "قيد الانتظار",
                "address": r["delivery_address"] if "delivery_address" in keys and r["delivery_address"] else "لم يحدد",
                "delivery_address": r["delivery_address"] if "delivery_address" in keys and r["delivery_address"] else "لم يحدد",
                "delivery_fee": r["delivery_fee"] if "delivery_fee" in keys and r["delivery_fee"] else 0.0,
                "created_at": r["created_at"] if "created_at" in keys and r["created_at"] else "",
            })
        return orders


def create_manual_delivery_order(customer_name, customer_phone, address, total_amount, delivery_fee=0.0):
    """
    إضافة طلب دليفري يدويًا من صفحة الدليفري نفسها (من غير المرور بصفحة البيع).
    بيتسجل كفاتورة (sale) بنفس منطق باقي الطلبات عشان يظهر في التقارير وجدول الشهر.
    """
    customer_id = get_or_create_customer(customer_name, customer_phone, address)
    now = datetime.now().isoformat(timespec="seconds")
    subtotal = max(total_amount - delivery_fee, 0.0)

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO sales (subtotal, discount, total, payment_type, customer_id, paid, paid_at,
                                   created_at, paid_amount, delivery_status, delivery_address, delivery_fee)
               VALUES (?, 0, ?, 'دليفري', ?, 0, NULL, ?, 0, 'قيد الانتظار', ?, ?)""",
            (subtotal, total_amount, customer_id, now, address, delivery_fee),
        )
        sale_id = cur.lastrowid
        conn.execute(
            """INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit, unit_price)
               VALUES (?, NULL, ?, 1, 'قطعة', ?)""",
            (sale_id, "طلب دليفري (مضاف يدويًا)", subtotal),
        )
    return sale_id


def update_delivery_status(sale_id, new_status):
    """تحديث حالة طلب الدليفري"""
    with get_connection() as conn:
        conn.execute("UPDATE sales SET delivery_status = ? WHERE id = ?", (new_status, sale_id))


def update_delivery_payment_and_status(sale_id, payment_type, total_amount=None, status="تم التسليم"):
    """
    تحديث حالة طلب الدليفري وطريقة الدفع.
    عند التسليم نقدي/محفظة يتم تسجيل المبلغ كمتحصل.
    """
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
        if not sale:
            return

        amt = total_amount if total_amount is not None else sale["total"]

        if status == "تم التسليم":
            if payment_type in ["نقدي", "محفظة"]:
                conn.execute(
                    """UPDATE sales SET delivery_status=?, payment_type=?, paid=1, paid_amount=?, paid_at=?
                       WHERE id=?""",
                    (status, payment_type, amt, now, sale_id),
                )
                existing_paid = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) AS t FROM sale_payments WHERE sale_id = ?", (sale_id,)
                ).fetchone()["t"]
                diff = amt - existing_paid
                if diff > EPSILON:
                    conn.execute(
                        "INSERT INTO sale_payments (sale_id, amount, created_at) VALUES (?, ?, ?)",
                        (sale_id, diff, now),
                    )
            else:  # آجل
                conn.execute(
                    "UPDATE sales SET delivery_status=?, payment_type=? WHERE id=?",
                    (status, payment_type, sale_id),
                )
        else:
            conn.execute(
                "UPDATE sales SET delivery_status=?, payment_type=? WHERE id=?",
                (status, payment_type, sale_id),
            )
def clear_all_customers():
    """مسح بيانات العملاء وعناوينهم وأرقامهم من كافة الجداول"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # 1. مسح جدول العملاء
        cursor.execute("DELETE FROM customers;")
        
        # 2. تفريغ بيانات العملاء والعناوين من جدول المبيعات القديمة
        try:
            cursor.execute("""
                UPDATE sales 
                SET customer_name = NULL, 
                    customer_phone = NULL, 
                    customer_address = NULL;
            """)
        except Exception as e:
            print(f"Sales update info: {e}")

        # إعادة تعيين الترقيم
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='customers';")
        except Exception:
            pass
            
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
    print("تم مسح كافة سجلات وأرقام العملاء بنجاح!")

# تشغيل الدالة
# clear_all_customers()