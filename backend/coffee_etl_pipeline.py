import os
import sys

# Keep this to help Git Bash find Python
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, sum as _sum, count, round

def clean_column_names(df):
    for c in df.columns:
        clean_name = c.lower().strip().replace(" ", "_").replace(".", "")
        df = df.withColumnRenamed(c, clean_name)
    return df

def run_pipeline():
    print("Starting Coffee Shop ETL Pipeline...")

    # Look how clean this is now! No jar configs needed.
    spark = SparkSession.builder \
        .appName("CoffeeAnalyticsETL") \
        .getOrCreate()

    # 2. EXTRACT: Load the three CSV files
    try:
        orders_df = spark.read.csv("data/orders.csv", header=True, inferSchema=True)
        customers_df = spark.read.csv("data/customers.csv", header=True, inferSchema=True)
        products_df = spark.read.csv("data/products.csv", header=True, inferSchema=True)
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return

    # Clean column names for all DataFrames
    orders_df = clean_column_names(orders_df)
    customers_df = clean_column_names(customers_df)
    products_df = clean_column_names(products_df)

    # 3. TRANSFORM: Enrich and Aggregate the data
    
    orders_df = orders_df.withColumn("order_date", to_date(col("order_date")))

    orders_df = orders_df.dropna(subset=["order_id", "product_id", "customer_id"])

    orders_df = orders_df.drop("unit_price")

    enriched_orders = orders_df.join(products_df, on="product_id", how="left")

    # --- NEW DATA ENGINEERING STEP ---
    # Calculate Sales (Quantity * Unit Price) AND Total Profit (Quantity * Unit Profit)
    # (Note: make sure your column is exactly named "unit_price" in your products csv)
    enriched_orders = enriched_orders.withColumn(
        "sales", 
        round(col("quantity") * col("unit_price"), 2)
    ).withColumn(
        "total_profit", 
        round(col("quantity") * col("profit"), 2)
    )

    # AGGREGATION A: Daily Sales & Profit
    daily_sales_df = enriched_orders.groupBy("order_date") \
        .agg(
            round(_sum("sales"), 2).alias("total_sales"),
            round(_sum("total_profit"), 2).alias("total_profit"),
            count("order_id").alias("total_orders")
        ).orderBy(col("order_date").desc())

    # AGGREGATION B: Customer Lifetime Value (Who are our best customers?)
    customer_ltv_df = enriched_orders.drop("customer_name").join(customers_df, on="customer_id", how="left") \
        .groupBy("customer_id", "customer_name", "loyalty_card") \
        .agg(
            round(_sum("sales"), 2).alias("lifetime_spent"),
            count("order_id").alias("total_purchases")
        ).orderBy(col("lifetime_spent").desc())

    print("Data transformations complete. Loading to database...")

    # 4. LOAD: Write to PostgreSQL
    DB_PROPERTIES = {
        "user": "postgres",           
        "password": "Vedansh1a@",   
        "driver": "org.postgresql.Driver"
    }
    DB_URL = "jdbc:postgresql://localhost:5432/ecommerce_db"

    # Write DataFrames to Postgres tables
    print("Writing Daily Sales Table...")
    daily_sales_df.write.jdbc(url=DB_URL, table="daily_sales", mode="overwrite", properties=DB_PROPERTIES)

    print("Writing Customer LTV Table...")
    customer_ltv_df.write.jdbc(url=DB_URL, table="customer_ltv", mode="overwrite", properties=DB_PROPERTIES)

    print("ETL Pipeline completed successfully! Data is ready for the API.")
    spark.stop()

if __name__ == "__main__":
    run_pipeline()