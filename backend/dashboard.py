import streamlit as st
import requests
import pandas as pd
import altair as alt

# --- CONFIGURATION ---
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Employee Portal", page_icon="🔐", layout="wide")

# --- SESSION STATE INITIALIZATION ---
# This checks if the user has a token. If not, it sets it to None.
if "token" not in st.session_state:
    st.session_state.token = None

def logout():
    """Wipes the token from memory to securely log the user out."""
    st.session_state.token = None
    st.rerun() # Forces the page to refresh

# --- VIEW 1: THE LOGIN PAGE ---
def show_login_page():
    st.title("🔐 Secure Employee Portal")
    st.markdown("Please log in with your employee credentials to access analytics.")
    
    # We use a form so the user can hit "Enter" to submit
    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            # Crucial System Design Note: FastAPI's OAuth2 expects Form Data, not JSON!
            # So we use `data=` instead of `json=` in our request.
            login_data = {"username": email, "password": password}
            
            try:
                response = requests.post(f"{API_BASE_URL}/login", data=login_data)
                
                if response.status_code == 200:
                    # Success! Grab the token and save it to the Session State
                    st.session_state.token = response.json()["access_token"]
                    st.success("Login successful! Redirecting...")
                    st.rerun() # Refresh to load the dashboard view
                else:
                    st.error("Invalid email or password. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the backend server. Is Uvicorn running?")


# --- VIEW 2: THE DASHBOARD PAGE ---
def show_dashboard():
    # Header with a Logout button
    col1, col2 = st.columns([8, 1])
    with col1:
        st.title("📈 Executive Analytics Dashboard")
    with col2:
        st.button("Logout", on_click=logout, use_container_width=True)
    
    st.divider()

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        # 1. Fetch BOTH datasets from FastAPI concurrently
        sales_response = requests.get(f"{API_BASE_URL}/sales", headers=headers)
        customers_response = requests.get(f"{API_BASE_URL}/customers/top", headers=headers)
        
        if sales_response.status_code in [401, 403]:
            st.error("Your session has expired or you are not authorized. Please log in again.")
            logout()
            return
            
        sales_data = sales_response.json().get("sales", [])
        top_customers = customers_response.json().get("top_customers", [])
        
        # 2. Render Top-Level KPI Cards using Pandas to do the math
        if sales_data:
            df_sales = pd.DataFrame(sales_data)
            total_revenue = df_sales['total_sales'].sum()
            avg_daily_revenue = df_sales['total_sales'].mean()
            
            # Create 3 columns for our metric cards
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric(label="Total Lifetime Revenue", value=f"${total_revenue:,.2f}")
            kpi2.metric(label="Avg Daily Revenue", value=f"${avg_daily_revenue:,.2f}")
            kpi3.metric(label="Total Selling Days", value=f"{len(df_sales)} Days")
            
            st.divider()
            
            # 3. Render the Charts side-by-side
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("Daily Revenue Timeline")
                # Streamlit automatically handles the axes if we set the index!
                st.line_chart(df_sales.set_index('sale_date')['total_sales'])
                
            with chart_col2:
                if top_customers:
                    st.subheader("Top Customers (LTV)")
                    df_customers = pd.DataFrame(top_customers)
                    st.bar_chart(df_customers.set_index('customer_name')['lifetime_spent'])
                else:
                    st.info("No customer data available yet.")
        else:
            st.info("No sales data available yet. Waiting for customer orders!")
            
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")


# --- MAIN APP ROUTING LOGIC ---
# This acts as the "Traffic Cop" deciding which view to show
if st.session_state.token is None:
    show_login_page()
else:
    show_dashboard()