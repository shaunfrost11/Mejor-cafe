import psycopg2
import sys

DATABASE_URL = "postgresql://neondb_owner:npg_9Zxsw6aVWIXj@ep-winter-waterfall-ao574vu5.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

def setup_cloud():
    try:
        print("🔌 Attempting to force connection to Neon Cloud...")
        # We bypass the environment variable and go straight to the source
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        print("🏗️ Creating tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                image_url TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                total_amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id),
                product_id INTEGER REFERENCES products(product_id),
                quantity INTEGER NOT NULL
            );
        """)

        print("☕ Stocking the coffee menu...")
        cursor.execute("TRUNCATE TABLE products CASCADE;")
        
        products = [
            ("Oat Milk Latte", "Creamy espresso with premium oat milk.", 5.50, "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=600&q=80"),
            ("Ethiopian Yirgacheffe", "Light roast with floral and citrus notes.", 18.50, "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?auto=format&fit=crop&w=600&q=80"),
            ("Colombian Dark Roast", "Bold, smoky, and chocolatey.", 15.00, "https://images.unsplash.com/photo-1611162458324-aae1eb4129a4?auto=format&fit=crop&w=600&q=80"),
            ("Vanilla Bean Frappuccino", "Ice-blended sweet vanilla coffee topped with whipped cream.", 5.50, "https://images.pexels.com/photos/1193335/pexels-photo-1193335.jpeg?auto=compress&cs=tinysrgb&w=600&bust=1"),
            ("Matcha Green Tea Latte", "Premium ceremonial grade matcha steeped with steamed milk.", 6.50, "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80"),
            ("Butter Croissant", "Flaky, golden-baked, and imported from France.", 4.50, "https://images.pexels.com/photos/3780469/pexels-photo-3780469.jpeg?auto=compress&cs=tinysrgb&w=600&bust=1"),
            ("Double Chocolate Tart", "Rich dark chocolate ganache in a crisp pastry shell.", 7.00, "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?auto=format&fit=crop&w=600&q=80"),
            ("Strawberry Macarons (3-pack)", "Delicate almond meringues filled with fresh strawberry buttercream.", 8.50, "https://images.unsplash.com/photo-1569864358642-9d1684040f43?auto=format&fit=crop&w=600&q=80")
        ]

        for p in products:
            cursor.execute("INSERT INTO products (name, description, price, image_url) VALUES (%s, %s, %s, %s)", p)

        conn.commit()
        print("✅ Success! Cloud database is fully built and populated.")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 TIP: If you see 'DNS name not found', try toggling Airplane Mode on/off on your phone to reset the IP.")

    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    setup_cloud()