import os
import sqlite3

# تحديد المسار المطلق لضمان الاتصال بملف shop.db الصحيح
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # التحقق من الأعمدة الموجودة في جدول المنتجات
    cursor.execute("PRAGMA table_info(products)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    # التأكد من وجود عمود الوحدة (unit)
    if "unit" not in existing_columns:
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'قطعة'")
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("تم التأكد من تهيئة هيكل جدول المنتجات بنجاح بدون إضافة بيانات افتراضية.")

if __name__ == "__main__":
    seed_database()