import sqlite3
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Pydantic models
class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    phone: str

class Order(BaseModel):
    id: Optional[int] = None
    cust_id: int
    notes: Optional[str] = None
    timestamp: Optional[int] = None
    items: List[int] = []

# Utilities
def open_db():
    connection = sqlite3.connect("dosa.db")
    cursor = connection.cursor()
    return (connection, cursor)

def close_db(connection):
    connection.commit()
    connection.close()

async def get_order_items(cursor, order_id: int):
    items = cursor.execute("SELECT name, price FROM items, item_list WHERE id=item_id AND order_id=?;", (order_id,)).fetchall()
    if items:
        formatted_items = []
        for item in items:
            formatted_items.append({
                "name": item[0],
                "price": item[1]
            })
        return formatted_items
    else:
        return []

async def format_order_rows_to_dict(cursor, rows):
    formatted_rows = []
    for row in rows:
        formatted_rows.append({
            "id": row[0],
            "timestamp": row[1],
            "name": row[2],
            "phone": row[3],
            "notes": row[4],
            "items": await get_order_items(cursor, row[0])
        })
    return formatted_rows

# API endpoints
@app.get("/customers")
def get_customers():
    (connection, cursor) = open_db()
    rows = cursor.execute("SELECT * FROM customers;").fetchall()
    close_db(connection)
    if rows:
        customers = []
        for row in rows:
            customers.append({
                "id": row[0],
                "name": row[1],
                "phone": row[2]
            })
        return customers
    else:
        raise HTTPException(status_code=404, detail="No customers found")

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    (connection, cursor) = open_db()
    row = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
    close_db(connection)
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "phone": row[2]
        }
    else:
        raise HTTPException(status_code=404, detail="Customer not found")

@app.put("/customers/{customer_id}")
def update_customer(customer_id: int, customer: Customer):
    if int(customer.id) != int(customer_id):
        raise HTTPException(status_code=400, detail="Customer ID in path and body must match")
    try:
        (connection, cursor) = open_db()
        cursor.execute("UPDATE customers SET name = ?, phone = ? WHERE id = ?;", (customer.name, customer.phone, customer_id))
        updated_customer = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
        close_db(connection)
        return {
            "id": updated_customer[0],
            "name": updated_customer[1],
            "phone": updated_customer[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")
    finally:
        close_db(connection)

@app.get("/items")
def get_items():
    (connection, cursor) = open_db()
    rows = cursor.execute("SELECT * FROM items;").fetchall()
    close_db(connection)
    if rows:
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "name": row[1],
                "price": row[2]
            })
        return items
    else:
        raise HTTPException(status_code=404, detail="No items found")

@app.get("/items/{item_id}")
def get_item(item_id: int):
    (connection, cursor) = open_db()
    row = cursor.execute("SELECT * FROM items WHERE id = ?;", (item_id,)).fetchone()
    close_db(connection)
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "price": row[2]
        }
    return 'Not implemented'

@app.get("/orders")
async def get_orders():
    (connection, cursor) = open_db()
    orders = cursor.execute("SELECT orders.id, timestamp, name, phone, notes FROM orders, customers WHERE customers.id=cust_id;").fetchall()

    order_list = await format_order_rows_to_dict(cursor, orders)
    close_db(connection)
    if order_list:
        return order_list
    else:
        raise HTTPException(status_code=404, detail="No orders found")

@app.post("/orders")
async def create_order(order: Order):
    (connection, cursor) = open_db()

    try:
        # Validate that the customer exists
        customer = cursor.execute("SELECT id FROM customers WHERE id = ?;", (order.cust_id,)).fetchone()
        if not customer:
            connection.rollback()
            connection.close()
            raise HTTPException(status_code=404, detail="Customer not found")

        # Validate that order has at least one item
        if not order.items:
            connection.rollback()
            connection.close()
            raise HTTPException(
                status_code=400,
                detail="Order must contain at least one item."
            )

        # Validate all item IDs exist before inserting anything
        item_ids = order.items
        placeholders = ','.join(['?'] * len(item_ids))
        existing_items = cursor.execute(
            f"SELECT id FROM items WHERE id IN ({placeholders});",
            item_ids
        ).fetchall()
        existing_item_ids = {row[0] for row in existing_items}

        # Check for invalid item IDs
        invalid_item_ids = [item_id for item_id in item_ids if item_id not in existing_item_ids]
        if invalid_item_ids:
            connection.rollback()
            connection.close()
            raise HTTPException(
                status_code=404,
                detail=f"Invalid item IDs: {invalid_item_ids}"
            )

        # Insert the order
        cursor.execute("INSERT INTO orders (cust_id, notes) VALUES (?, ?);",
                      (order.cust_id, order.notes))
        order_id = cursor.lastrowid

        # Insert items into item_list
        for item_id in order.items:
            cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);",
                              (order_id, item_id))

        # Fetch the created order with customer details
        created_order = cursor.execute("""
        SELECT orders.id, timestamp, name, phone, notes
        FROM orders, customers
        WHERE customers.id=cust_id AND orders.id=?;
        """, (order_id,)).fetchone()

        formatted_order = await format_order_rows_to_dict(cursor, [created_order])
        close_db(connection)

        return formatted_order[0]
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback on any other error
        connection.rollback()
        connection.close()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    (connection, cursor) = open_db()
    order = cursor.execute("""
    SELECT orders.id, timestamp, name, phone, notes
    FROM orders, customers
    WHERE customers.id=cust_id AND orders.id=?;
    """, (order_id,)).fetchone()
    order = await format_order_rows_to_dict(cursor, [order])
    close_db(connection)
    if len(order) > 0:
        return order[0]
    else:
        raise HTTPException(status_code=404, detail="Order not found")

@app.get("/item_list")
def get_item_list():
    (connection, cursor) = open_db()
    rows = cursor.execute("SELECT order_id, item_id FROM item_list;").fetchall()
    close_db(connection)
    if rows:
        item_list = []
        for row in rows:
            item_list.append({
                "order_id": row[0],
                "item_id": row[1]
            })
        return item_list
    else:
        raise HTTPException(status_code=404, detail="No item list entries found")
