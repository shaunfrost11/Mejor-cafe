import psycopg2

conn = psycopg2.connect(
    dbname="ecommerce_db",
    user="postgres",
    password="Vedansh1a@",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

try:
    # 1. Add the new image_url column
    cursor.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);")

    # 2. Fresh, verified Unsplash links for the entire menu
    images = {
        "Vanilla Bean Frappuccino": "https://images.unsplash.com/photo-1664580665322-a9b0c0349cc9?auto=format&fit=crop&w=600&q=80", # Iced Frappuccino
        "Matcha Green Tea Latte": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?auto=format&fit=crop&w=600&q=80",
        "Butter Croissant": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80", # Fresh Croissant
        "Double Chocolate Tart": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80",
        "Strawberry Macarons (3-pack)": "https://images.unsplash.com/photo-1569864358642-9d1684040f43?auto=format&fit=crop&w=600&q=80",
    }

    # 3. Update existing products with their specific images
    for name, url in images.items():
        cursor.execute("UPDATE products SET image_url = %s WHERE name = %s;", (url, name))

    # 4. Set a safe fallback image for any older items (like your original coffees)
    fallback_url = "https://images.unsplash.com/photo-1498804103079-a6351b050096?auto=format&fit=crop&w=600&q=80"
    cursor.execute("UPDATE products SET image_url = %s WHERE image_url IS NULL;", (fallback_url,))

    conn.commit()
    print("✅ Database upgraded! Image URLs are now natively stored.")
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()