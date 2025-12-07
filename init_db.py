import sqlite3
import json

# Helper functions

# Initialize the database from example-orders.json
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

    def list_customers():
        rows = cursor.execute("SELECT id, name, phone FROM customers;").fetchall()
        return rows

    def list_items():
        rows = cursor.execute("SELECT id, name, price FROM items;").fetchall()
        return rows

    def list_orders():
        rows = cursor.execute("SELECT id, timestamp, cust_id, notes FROM orders;").fetchall()
        return rows

    def list_item_list():
        rows = cursor.execute("SELECT order_id, item_id FROM item_list;").fetchall()
        return rows

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


    # Load data from example-orders.json
    with open("./data/example_orders.json", "r") as f:
        orders = json.load(f)

    # Insert data into tables
    # Seed customers
    with open("./data/customers.json", "r") as f:
        customers = json.load(f)
    for phone, name in customers.items():
        add_customer(name, phone)

    # Seed items
    with open("./data/items.json", "r") as f:
        items = json.load(f)
    for name, item in items.items():
        add_item(name, item["price"])

    # Seed orders and item list
    for order in orders:
        timestamp = order["timestamp"]
        notes = order["notes"]
        name = order["name"]
        phone = order["phone"]
        cust_id = cursor.execute("SELECT id FROM customers WHERE phone = ?;", (phone,)).fetchone()[0]
        add_order(timestamp, cust_id, notes)
        order_id = cursor.lastrowid
        for item in order["items"]:
            if item["name"] not in list_items():
                add_item(item["name"], item["price"])
                item_id = cursor.lastrowid
                add_item_list(order_id, item_id)
            else:
                item_id = cursor.execute("SELECT id FROM items WHERE name = ?;", (item["name"],)).fetchone()[0]
                add_item_list(order_id, item_id)

    # Print the data
    # print(list_customers())
    # print(list_items())
    # print(list_orders())
    # print(list_item_list())
    print("Customers:")
    print(count_customers())
    print("Items:")
    print(count_items())
    print("Orders:")
    print(count_orders())
    print("Item List:")
    print(count_item_list())

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()
