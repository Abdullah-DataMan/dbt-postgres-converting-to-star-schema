import psycopg2
from faker import Faker
import random

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

# Create Schema and Tables matching the exact schema diagram
create_tables_query = """
DROP SCHEMA IF EXISTS staging_schema CASCADE;
CREATE SCHEMA staging_schema;

-- 1. Product Lines
CREATE TABLE staging_schema.productlines (
    productLine VARCHAR(50) PRIMARY KEY,
    textDescription TEXT,
    htmlDescription TEXT,
    image BYTEA
);

-- 2. Offices
CREATE TABLE staging_schema.offices (
    officeCode VARCHAR(50) PRIMARY KEY,
    city VARCHAR(50),
    phone VARCHAR(50),
    addressLine1 VARCHAR(50),
    addressLine2 VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postalCode VARCHAR(50),
    territory VARCHAR(50)
);

-- 3. Employees
CREATE TABLE staging_schema.employees (
    employeeNumber INT PRIMARY KEY,
    lastName VARCHAR(50),
    firstName VARCHAR(50),
    extension VARCHAR(50),
    email VARCHAR(100),
    officeCode VARCHAR(50) REFERENCES staging_schema.offices(officeCode),
    reportsTo INT,
    jobTitle VARCHAR(50)
);

-- 4. Products
CREATE TABLE staging_schema.products (
    productCode VARCHAR(50) PRIMARY KEY,
    productName VARCHAR(100),
    productLine VARCHAR(50) REFERENCES staging_schema.productlines(productLine),
    productScale VARCHAR(50),
    productVendor VARCHAR(50),
    productDescription TEXT,
    quantityInStock SMALLINT,
    buyPrice DECIMAL(10,2),
    MSRP DECIMAL(10,2)
);

-- 5. Customers
CREATE TABLE staging_schema.customers (
    customerNumber INT PRIMARY KEY,
    customerName VARCHAR(50),
    contactLastName VARCHAR(50),
    contactFirstName VARCHAR(50),
    phone VARCHAR(50),
    addressLine1 VARCHAR(50),
    addressLine2 VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    postalCode VARCHAR(50),
    country VARCHAR(50),
    salesRepEmployeeNumber INT REFERENCES staging_schema.employees(employeeNumber),
    creditLimit DECIMAL(10,2)
);

-- 6. Orders
CREATE TABLE staging_schema.orders (
    orderNumber INT PRIMARY KEY,
    orderDate DATE,
    requiredDate DATE,
    shippedDate DATE,
    status VARCHAR(50),
    comments TEXT,
    customerNumber INT REFERENCES staging_schema.customers(customerNumber)
);

-- 7. Order Details
CREATE TABLE staging_schema.orderdetails (
    orderNumber INT REFERENCES staging_schema.orders(orderNumber),
    productCode VARCHAR(50) REFERENCES staging_schema.products(productCode),
    quantityOrdered INT,
    priceEach DECIMAL(10,2),
    orderLineNumber SMALLINT,
    PRIMARY KEY (orderNumber, productCode)
);

-- 8. Payments
CREATE TABLE staging_schema.payments (
    customerNumber INT REFERENCES staging_schema.customers(customerNumber),
    checkNumber VARCHAR(50),
    paymentDate DATE,
    amount DECIMAL(10,2),
    PRIMARY KEY (customerNumber, checkNumber)
);
"""

cursor.execute(create_tables_query)
conn.commit()
print("Tables created successfully. Inserting dummy data...")

# Insert Dummy Data to satisfy foreign key dependencies
# --- Product Lines ---
p_lines = ["Classic Cars", "Motorcycles", "Planes", "Ships", "Trains"]
for line in p_lines:
    cursor.execute(
        "INSERT INTO staging_schema.productlines (productLine, textDescription) VALUES (%s, %s)",
        (line, fake.text())
    )

# --- Offices ---
office_codes = ["1", "2", "3"]
for code in office_codes:
    cursor.execute(
        "INSERT INTO staging_schema.offices (officeCode, city, country) VALUES (%s, %s, %s)",
        (code, fake.city(), fake.country())
    )

# --- Employees ---
emp_numbers = [1001, 1002, 1003]
for emp_id in emp_numbers:
    cursor.execute(
        "INSERT INTO staging_schema.employees (employeeNumber, lastName, firstName, officeCode) VALUES (%s, %s, %s, %s)",
        (emp_id, fake.last_name(), fake.first_name(), random.choice(office_codes))
    )

# --- Products ---
product_codes = [f"S{i}_100{i}" for i in range(1, 11)]
for p_code in product_codes:
    cursor.execute(
        "INSERT INTO staging_schema.products (productCode, productName, productLine, buyPrice, MSRP) VALUES (%s, %s, %s, %s, %s)",
        (p_code, fake.word().capitalize(), random.choice(p_lines), round(random.uniform(10, 100), 2), round(random.uniform(120, 200), 2))
    )

# --- Customers ---
cust_numbers = [101, 102, 103, 104, 105]
for c_num in cust_numbers:
    cursor.execute(
        "INSERT INTO staging_schema.customers (customerNumber, customerName, city, country, salesRepEmployeeNumber) VALUES (%s, %s, %s, %s, %s)",
        (c_num, fake.company(), fake.city(), fake.country(), random.choice(emp_numbers))
    )

# --- Orders ---
order_numbers = [5001, 5002, 5003]
for o_num in order_numbers:
    cursor.execute(
        "INSERT INTO staging_schema.orders (orderNumber, orderDate, status, customerNumber) VALUES (%s, %s, %s, %s)",
        (o_num, fake.date_this_year(), "Shipped", random.choice(cust_numbers))
    )

# --- Order Details ---
for o_num in order_numbers:
    for idx, p_code in enumerate(random.sample(product_codes, 2), start=1):
        cursor.execute(
            "INSERT INTO staging_schema.orderdetails (orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber) VALUES (%s, %s, %s, %s, %s)",
            (o_num, p_code, random.randint(1, 10), round(random.uniform(50, 150), 2), idx)
        )

# --- Payments ---
for c_num in cust_numbers:
    cursor.execute(
        "INSERT INTO staging_schema.payments (customerNumber, checkNumber, paymentDate, amount) VALUES (%s, %s, %s, %s)",
        (c_num, f"HQ{random.randint(100000,999999)}", fake.date_this_year(), round(random.uniform(200, 1000), 2))
    )

conn.commit()
cursor.close()
conn.close()
print("Data inserted successfully!")