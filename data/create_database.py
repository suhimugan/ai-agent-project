import sqlite3
import os

def create_sample_database():
    db_path = "data/company.db"
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table 1: Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            plan TEXT NOT NULL,
            joined_date TEXT NOT NULL
        )
    """)

    # Table 2: Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Table 3: Support tickets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL,
            created_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Sample data: customers
    customers = [
        (1, "Alice Johnson",  "alice@example.com",  "Pro",        "2024-01-15"),
        (2, "Bob Smith",      "bob@example.com",     "Starter",    "2024-03-22"),
        (3, "Carol White",    "carol@example.com",   "Enterprise", "2023-11-08"),
        (4, "David Lee",      "david@example.com",   "Pro",        "2024-06-01"),
        (5, "Eva Martinez",   "eva@example.com",     "Starter",    "2025-01-10"),
    ]

    # Sample data: orders
    orders = [
        (1, 1, "Pro Plan",        12.00,  "completed", "2024-02-01"),
        (2, 1, "Pro Plan",        12.00,  "completed", "2024-03-01"),
        (3, 2, "Starter Upgrade", 0.00,   "completed", "2024-04-01"),
        (4, 3, "Enterprise Plan", 499.00, "completed", "2024-01-01"),
        (5, 4, "Pro Plan",        12.00,  "completed", "2024-06-15"),
        (6, 4, "Pro Plan",        12.00,  "refunded",  "2024-07-15"),
        (7, 5, "Starter Plan",    0.00,   "completed", "2025-01-10"),
    ]

    # Sample data: support tickets
    tickets = [
        (1, 1, "App crashes on startup",        "resolved", "2024-02-10"),
        (2, 2, "Cannot export data",            "open",     "2024-05-01"),
        (3, 3, "Billing issue with invoice",    "resolved", "2024-03-15"),
        (4, 4, "Refund request for July order", "resolved", "2024-07-16"),
        (5, 5, "Login not working",             "open",     "2025-01-12"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?)", customers)
    cursor.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders)
    cursor.executemany(
        "INSERT OR IGNORE INTO support_tickets VALUES (?,?,?,?,?)", tickets)

    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")
    print("Tables: customers, orders, support_tickets")


if __name__ == "__main__":
    create_sample_database()