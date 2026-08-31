import sqlite3

conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

# قائمة الجداول المراد إفراغها (المبيعات، الدليفري، المرتجعات، والمصروفات)
tables_to_clear = [
    "sale_items",
    "sales",
    "returns",
    "return_items",
    "expenses",
]

for table in tables_to_clear:
    try:
        cursor.execute(f"DELETE FROM {table};")
    except sqlite3.OperationalError:
        pass  # التجاوز في حال عدم وجود أحد الجداول بنفس الاسم

# تصفير عدادات الترقيم التلقائي للجداول الممحيّة
cursor.execute(
    """
    DELETE FROM sqlite_sequence 
    WHERE name IN ('sales', 'sale_items', 'returns', 'return_items', 'expenses');
"""
)

conn.commit()
conn.close()

print("تم مسح بيانات المبيعات، الدليفري، المرتجعات، والتقارير بنجاح!")