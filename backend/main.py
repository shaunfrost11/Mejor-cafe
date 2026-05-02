from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from security import get_password_hash, verify_password, create_access_token
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from security import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordRequestForm
from typing import List  
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware  
import os 
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Coffee Shop Analytics API")

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",  
    "https://mejorcafe.netlify.app", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = "localhost"
DB_NAME = "ecommerce_db"
DB_USER = "postgres"
DB_PASS = "Vedansh1a@" 


def get_db_connection():
    # 1. First, check if we are in the cloud and have a secret URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # We are in the cloud! Use the cloud URL.
        return psycopg2.connect(database_url)
    else:
        # We are on your laptop! Fall back to the local database.
        return psycopg2.connect(
            dbname="ecommerce_db",
            user="postgres",
            password="Vedansh1a@", # Make sure this is your actual local password
            host="localhost",
            port="5432"
        )

# This tells FastAPI to look for the "Bearer" token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    The Bouncer: Decodes the JWT, verifies the signature, 
    and checks if the user is still valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the "VIP Badge" using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: str = payload.get("id")

        if email is None or role is None:
            raise credentials_exception
            
        return {"email": email, "role": role, "id":user_id}
        
    except jwt.PyJWTError:
        raise credentials_exception

# --- DATA MODELS (Data Validation) ---
class UserCreate(BaseModel):
    email: str
    password: str
    role: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/register")
def register_user(user: UserCreate):
    print(f"DEBUG - What did the server actually receive? {user.password}")
    """Registers a new employee or customer and hashes their password."""
    # 1. Encrypt the password immediately
    hashed_pw = get_password_hash(user.password)
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database error")
    
    cursor = conn.cursor()
    try:
        # 2. Insert into the database
        cursor.execute(
            """INSERT INTO users (email, password_hash, role, full_name) 
               VALUES (%s, %s, %s, %s) RETURNING user_id;""",
            (user.email, hashed_pw, user.role, user.full_name)
        )
        new_user_id = cursor.fetchone()[0]
        conn.commit()
        return {"message": "Account created successfully!", "user_id": new_user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email already registered or invalid data.")
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Verifies credentials and hands out the JWT VIP Badge."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Find the user by email
    cursor.execute("SELECT user_id, email, password_hash, role FROM users WHERE email = %s;", (form_data.username,))
    db_user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    # 2. Security Check: Does the user exist? Does the password match?
    if not db_user or not verify_password(form_data.password, db_user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # 3. Success! Generate the JWT Token payload
    token_data = {
        "sub": db_user['email'], 
        "role": db_user['role'], 
        "id": str(db_user['user_id'])
    }
    access_token = create_access_token(data=token_data)
    
    # 4. Hand the badge to the frontend
    return {"access_token": access_token, "token_type": "bearer", "role": db_user['role']}

# --- PRODUCT & MENU ROUTES ---

@app.get("/products")
def get_products():
    """Returns the full menu for the customer storefront."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM products WHERE is_active = TRUE;")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"products": products}

@app.get("/products/{product_id}")
def get_product_details(product_id: str):
    """Fetches details for a specific product and its reviews."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Get Product Info
    cursor.execute("SELECT * FROM products WHERE product_id = %s;", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # 2. Get associated Reviews
    cursor.execute("""
        SELECT r.rating, r.comment, r.created_at, u.full_name 
        FROM reviews r 
        JOIN users u ON r.customer_id = u.user_id 
        WHERE r.product_id = %s 
        ORDER BY r.created_at DESC;
    """, (product_id,))
    reviews = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return {"product": product, "reviews": reviews}

# --- CUSTOMER REVIEW POSTING (Protected) ---

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    comment: str

@app.post("/reviews")
def post_review(review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    print(f"\n--- DEBUG CURRENT USER --- \n{current_user}\n")
    """Allows a logged-in customer to leave a review."""
    # Only customers can review!
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only registered customers can leave reviews")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO reviews (product_id, customer_id, rating, comment) VALUES (%s, %s, %s, %s);",
            (review.product_id, current_user["id"], review.rating, review.comment)
        )
        conn.commit()
        return {"message": "Review posted successfully!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/")
def home():
    return {"message": "Welcome to the Coffee Shop Data API! The server is live."}

# --- EMPLOYEE ANALYTICS ROUTES (Protected) ---

@app.get("/sales")
def get_daily_sales(current_user: dict = Depends(get_current_user)):
    """Calculates total revenue grouped by day."""
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Employees only")
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # We group the orders by date to draw a nice timeline chart
    cursor.execute("""
        SELECT DATE(created_at) as sale_date, SUM(total_amount) as total_sales
        FROM orders
        GROUP BY DATE(created_at)
        ORDER BY sale_date ASC;
    """)
    sales = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return {"sales": sales}

@app.get("/customers/top")
def get_top_customers(current_user: dict = Depends(get_current_user)):
    """Calculates the lifetime value (LTV) of customers."""
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Employees only")
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Join users and orders to find who spent the most money
    cursor.execute("""
        SELECT u.full_name as customer_name, SUM(o.total_amount) as lifetime_spent
        FROM orders o
        JOIN users u ON o.customer_id = u.user_id
        GROUP BY u.user_id, u.full_name
        ORDER BY lifetime_spent DESC
        LIMIT 10;
    """)
    top_customers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return {"top_customers": top_customers}

# --- CHECKOUT & CART ROUTES ---

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CheckoutRequest(BaseModel):
    items: List[CartItem]

@app.post("/checkout")
def checkout(request: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    """Processes a shopping cart, calculates totals securely, and creates an order."""
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can checkout.")
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Step 1: Calculate the true total and verify stock
        total_amount = 0
        verified_items = []
        
        for item in request.items:
            cursor.execute("SELECT price, stock_quantity FROM products WHERE product_id = %s;", (item.product_id,))
            product = cursor.fetchone()
            
            if not product:
                raise ValueError(f"Product {item.product_id} not found.")
            if product['stock_quantity'] < item.quantity:
                raise ValueError(f"Not enough stock for product {item.product_id}.")
                
            item_total = product['price'] * item.quantity
            total_amount += item_total
            
            verified_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": product['price']
            })

        # Step 2: Create the main Order record (FIXED VARIABLES HERE)
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s) RETURNING order_id;",
            (current_user['user_id'], total_amount, 'completed') 
        )
        new_order_id = cursor.fetchone()['order_id']
        
        # Step 3: Insert all Order Items and deduct inventory stock
        for item in verified_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
                (new_order_id, item['product_id'], item['quantity'])
            )
            cursor.execute(
                "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s;",
                (item['quantity'], item['product_id'])
            )

        # Step 4: SUCCESS! Commit the transaction
        conn.commit()
        return {
            "message": "Checkout successful!", 
            "order_id": str(new_order_id), 
            "total_charged": float(total_amount)
        }
        
    except ValueError as ve:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        conn.rollback()
        print(f"DEBUG ERROR: {e}") # This will print the exact reason to Render if it fails again
        raise HTTPException(status_code=500, detail="An internal error occurred during checkout.")
    finally:
        cursor.close()
        conn.close()
        
@app.get("/my-orders")
def get_my_orders(current_user: dict = Depends(get_current_user)):
    """Returns a list of past orders for the logged-in customer."""
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Employees do not have order histories.")
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Notice we use their token's ID so they can only see THEIR orders
    cursor.execute("""
        SELECT order_id, total_amount, status, created_at 
        FROM orders 
        WHERE customer_id = %s 
        ORDER BY created_at DESC;
    """, (current_user["id"],))
    
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return {"my_orders": orders}