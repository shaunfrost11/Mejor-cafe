import psycopg2

# Connect to your database
conn = psycopg2.connect(
    dbname="ecommerce_db",
    user="postgres",
    password="Vedansh1a@", # Make sure this matches your DB password!
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Switching to Pexels, which doesn't block localhost testing!
# We also added "&bust=1" to the end. This tricks your browser into thinking 
# it's a completely new file it has never seen before, forcing a fresh download.
new_images = {
    "Vanilla Bean Frappuccino": "https://images.pexels.com/photos/1193335/pexels-photo-1193335.jpeg?auto=compress&cs=tinysrgb&w=600&bust=1",
    "Butter Croissant": "https://images.pexels.com/photos/3780469/pexels-photo-3780469.jpeg?auto=compress&cs=tinysrgb&w=600&bust=1"
}

try:
    print("🔧 Applying the Pexels cache-buster patch...")
    
    for name, url in new_images.items():
        cursor.execute("UPDATE products SET image_url = %s WHERE name = %s;", (url, name))
        print(f"  - Successfully updated: {name}")

    conn.commit()
    print("\n✅ Patch complete!")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")

finally:
    cursor.close()
    conn.close()