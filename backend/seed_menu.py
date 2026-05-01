import psycopg2

# 1. Connect to your database (Update with your actual password if different)
conn = psycopg2.connect(
    dbname="ecommerce_db",
    user="postgres",
    password="Vedansh1a@", # Change this to your DB password
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# 2. The New Mejor Cafe Menu
new_products = [
    ("Vanilla Bean Frappuccino", "Ice-blended sweet vanilla coffee topped with whipped cream.", 5.50, 40),
    ("Matcha Green Tea Latte", "Premium ceremonial grade matcha steamed with oat milk.", 6.00, 30),
    ("Butter Croissant", "Flaky, golden-baked, and imported from France.", 3.50, 20),
    ("Double Chocolate Tart", "Rich dark chocolate ganache in a crisp pastry shell.", 5.00, 15),
    ("Strawberry Macarons (3-pack)", "Delicate almond meringue shells filled with fresh strawberry buttercream.", 6.50, 25)
]

# 3. Insert them into the database
try:
    for item in new_products:
        cursor.execute(
            """INSERT INTO products (name, description, price, stock_quantity) 
               VALUES (%s, %s, %s, %s);""",
            item
        )
    conn.commit()
    print("✅ Success! Mejor Cafe menu has been expanded.")
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()