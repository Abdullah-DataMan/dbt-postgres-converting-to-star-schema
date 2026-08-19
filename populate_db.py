import psycopg2
from faker import Faker
import random

# Initialize Faker library for synthetic data generation
fake = Faker()

# Connect to PostgreSQL running inside the Docker container
conn = psycopg2.connect(
    host="127.0.0.1",
    database="retail_db",
    user="admin",
    password="adminpassword",
    port="5432"
)
cursor = conn.cursor()

print("Connected to PostgreSQL successfully.")

# 1. Create Schema and Tables
create_tables_query = """
CREATE SCHEMA IF NOT EXISTS staging_schema;

-- Items Table
CREATE TABLE IF NOT EXISTS staging_schema.Items (
    sku VARCHAR(50) PRIMARY KEY,
    price DECIMAL(10, 2),
    name VARCHAR(255),
    brand VARCHAR(100)
);

-- Stores Table
CREATE TABLE IF NOT EXISTS staging_schema.Stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(255),
    store_city VARCHAR(100),
    store_zipcode VARCHAR(20)
);

-- Customers Table
CREATE TABLE IF NOT EXISTS staging_schema.Customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    customer_zipcode VARCHAR(20)
);

-- Orders Table
CREATE TABLE IF NOT EXISTS staging_schema.Orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES staging_schema.Customers(customer_id),
    store_id INT REFERENCES staging_schema.Stores(store_id),
    order_date DATE
);

-- Order Items Table
CREATE TABLE IF NOT EXISTS staging_schema.Order_Items (
    order_id INT REFERENCES staging_schema.Orders(order_id),
    item_line_number INT,
    item_sku VARCHAR(50) REFERENCES staging_schema.Items(sku),
    item_quantity INT,
    PRIMARY KEY (order_id, item_line_number)
);
"""
cursor.execute(create_tables_query)
conn.commit()
print("Schema and Tables created successfully.")

# 2. Insert Dummy Data
print("Inserting dummy data...")

# Insert 50 products
skus = []
for _ in range(50):
    sku = fake.unique.ean(length=8)
    skus.append(sku)
    cursor.execute(
        "INSERT INTO staging_schema.Items (sku, price, name, brand) VALUES (%s, %s, %s, %s)",
        (sku, round(random.uniform(10.0, 500.0), 2), fake.word().capitalize(), fake.company())
    )

# Insert 10 stores
store_ids = []
for _ in range(10):
    cursor.execute(
        "INSERT INTO staging_schema.Stores (store_name, store_city, store_zipcode) VALUES (%s, %s, %s) RETURNING store_id",
        (f"Store {fake.word().capitalize()}", fake.city(), fake.zipcode())
    )
    store_ids.append(cursor.fetchone()[0])

# Insert 100 customers
customer_ids = []
for _ in range(100):
    cursor.execute(
        "INSERT INTO staging_schema.Customers (customer_name, customer_zipcode) VALUES (%s, %s) RETURNING customer_id",
        (fake.name(), fake.zipcode())
    )
    customer_ids.append(cursor.fetchone()[0])

# Insert 100 orders, each linked to line items in Order_Items
for _ in range(100):
    cursor.execute(
        "INSERT INTO staging_schema.Orders (customer_id, store_id, order_date) VALUES (%s, %s, %s) RETURNING order_id",
        (random.choice(customer_ids), random.choice(store_ids), fake.date_this_year())
    )
    order_id = cursor.fetchone()[0]
    
    # Each order contains between 1 and 3 line items
    num_items = random.randint(1, 3)
    for line_num in range(1, num_items + 1):
        cursor.execute(
            "INSERT INTO staging_schema.Order_Items (order_id, item_line_number, item_sku, item_quantity) VALUES (%s, %s, %s, %s)",
            (order_id, line_num, random.choice(skus), random.randint(1, 5))
        )

# Commit changes and close database connection
conn.commit()
cursor.close()
conn.close()
print("100 records inserted successfully. Database is ready!")