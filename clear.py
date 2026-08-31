import sqlite3

# الاتصال بقاعدة البيانات مباشرة
conn = sqlite3.connect("shop.db")
cursor = conn.cursor()

# مسح المبيعات وعناصر الفواتير
cursor.execute("DELETE FROM sale_items;")
cursor.execute("DELETE FROM sales;")

# تصفير العداد لتبدأ الطلبات والفواتير من رقم 1
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('sales', 'sale_items');")

conn.commit()
conn.close()

print("تم إفراغ صفحة الدليفري وجدول الشهر بنجاح!")