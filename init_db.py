import sqlite3
import json

def init_db():
    # Open a connection to the database
    connection = sqlite3.connect("dosa.db")
    cursor = connection.cursor()

    # Create empty tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY,
        name CHAR(64) NOT NULL,
        phone CHAR(10) NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY,
        name CHAR(64) NOT NULL,
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
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

    # Helper functions
    def add_customer(name, phone):
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);",
                       (name, phone))

    def add_item(name, price):
        cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);",
                       (name, price))

    def add_order(timestamp, cust_id, notes):
        cursor.execute("INSERT INTO orders (timestamp, cust_id, notes) VALUES (?, ?, ?);",
                       (timestamp, cust_id, notes))

    def add_item_list(order_id, item_id):
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);",
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
    print(f"Added {count_customers()} customers to dosa.db")

    # Seed items
    with open("./data/items.json", "r") as f:
        items = json.load(f)
    for name, item in items.items():
        add_item(name, item["price"])
    print(f"Added {count_items()} items to dosa.db")

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
        add_order(timestamp, cust_id, notes)
        order_id = cursor.lastrowid
        items = cursor.execute("SELECT id, name, price FROM items;").fetchall()
        for item in order["items"]:
            if item["name"] not in [item[1] for item in items]:
                add_item(item["name"], item["price"])
                item_id = cursor.lastrowid
                add_item_list(order_id, item_id)
            else:
                item_id = cursor.execute("SELECT id FROM items WHERE name = ?;", (item["name"],)).fetchone()[0]
                add_item_list(order_id, item_id)
    print(f"Added {count_orders()} orders to dosa.db")
    print(f"Added {count_item_list()} item list entries to dosa.db")

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()
