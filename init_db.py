import sqlite3
import json

def init_db():
    # Open a connection to the database
    connection = sqlite3.connect("db.sqlite")
    # Ensure SQLite enforces foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON;")
    cursor = connection.cursor()

    # Create empty tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY,
        name CHAR(64) NOT NULL,
        phone CHAR(10) NOT NULL UNIQUE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY,
        name CHAR(64) NOT NULL UNIQUE,
        price REAL NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cust_id INT NOT NULL,
        notes TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS item_list(
        order_id NOT NULL,
        item_id NOT NULL,
        UNIQUE(order_id, item_id),
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

    # Helpful indices for better query performance as data grows
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_cust_id ON orders(cust_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_list_order_id ON item_list(order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_list_item_id ON item_list(item_id);")

    # Helper functions
    def add_customer(name, phone):
        # Use INSERT OR IGNORE to avoid duplicates
        cursor.execute("INSERT OR IGNORE INTO customers (name, phone) VALUES (?, ?);",
                       (name, phone))

    def add_item(name, price):
        # Use INSERT OR IGNORE to avoid duplicates, then always get the ID
        cursor.execute("INSERT OR IGNORE INTO items (name, price) VALUES (?, ?);",
                       (name, price))
        # Always fetch the ID (whether inserted or already existed)
        result = cursor.execute("SELECT id FROM items WHERE name = ?;", (name,)).fetchone()
        return result[0]

    def add_order(timestamp, cust_id, notes):
        # Check if order already exists and return its ID
        existing_order = cursor.execute("SELECT id FROM orders WHERE timestamp = ? AND cust_id = ? AND notes = ?;", (timestamp, cust_id, notes)).fetchone()
        if existing_order:
            return existing_order[0]
        cursor.execute("INSERT INTO orders (timestamp, cust_id, notes) VALUES (?, ?, ?);",
                       (timestamp, cust_id, notes))
        return cursor.lastrowid

    def add_item_list(order_id, item_id):
        # Use INSERT OR IGNORE to avoid duplicates
        cursor.execute("INSERT OR IGNORE INTO item_list (order_id, item_id) VALUES (?, ?);",
                       (order_id, item_id))

    def count_customers():
        rows = cursor.execute("SELECT COUNT(*) FROM customers;").fetchone()
        return rows[0]

    def count_items():
        rows = cursor.execute("SELECT COUNT(*) FROM items;").fetchone()
        return rows[0]

    def count_orders():
        rows = cursor.execute("SELECT COUNT(*) FROM orders;").fetchone()
        return rows[0]

    def count_item_list():
        rows = cursor.execute("SELECT COUNT(*) FROM item_list;").fetchone()
        return rows[0]

    # Insert data into tables
    # Seed customers
    with open("./data/customers.json", "r") as f:
        customers = json.load(f)
    for phone, name in customers.items():
        add_customer(name, phone)
    print(f"Added {count_customers()} customers to db.sqlite")

    # Seed items
    with open("./data/items.json", "r") as f:
        items = json.load(f)
    for name, item in items.items():
        add_item(name, item["price"])
    print(f"Added {count_items()} items to db.sqlite")

    # Load data from example-orders.json
    with open("./data/example_orders.json", "r") as f:
        orders = json.load(f)
    # Seed orders and item list
    for order in orders:
        timestamp = order["timestamp"]
        notes = order["notes"]
        name = order["name"]
        phone = order["phone"]
        cust_id = cursor.execute("SELECT id FROM customers WHERE phone = ?;", (phone,)).fetchone()[0]
        order_id = add_order(timestamp, cust_id, notes)
        for item in order["items"]:
            item_id = add_item(item["name"], item["price"])
            add_item_list(order_id, item_id)
    print(f"Added {count_orders()} orders to db.sqlite")
    print(f"Added {count_item_list()} item list entries to db.sqlite")

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()
