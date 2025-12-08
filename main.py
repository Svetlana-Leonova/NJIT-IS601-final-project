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

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    price: float

class Order(BaseModel):
    id: Optional[int] = None
    cust_id: int
    notes: Optional[str] = None
    timestamp: Optional[int] = None
    items: List[int] = []

# Utilities
def open_db():
    connection = sqlite3.connect("db.sqlite")
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
# Customers
@app.post("/customers")
def create_customer(customer: Customer):
    try:
        (connection, cursor) = open_db()
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);", (customer.name, customer.phone))
        customer_id = cursor.lastrowid
        created_customer = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
        close_db(connection)
        return {
            "id": created_customer[0],
            "name": created_customer[1],
            "phone": created_customer[2]
        }
    except sqlite3.IntegrityError as e:
        close_db(connection)
        raise HTTPException(status_code=400, detail=f"Error creating customer: Customer with this phone number already exists")
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")

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
    if customer.id is not None and int(customer.id) != int(customer_id):
        raise HTTPException(status_code=400, detail="Customer ID in path and body must match")
    try:
        (connection, cursor) = open_db()
        # Check if customer exists
        existing_customer = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
        if not existing_customer:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Customer not found")
        cursor.execute("UPDATE customers SET name = ?, phone = ? WHERE id = ?;", (customer.name, customer.phone, customer_id))
        updated_customer = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
        close_db(connection)
        return {
            "id": updated_customer[0],
            "name": updated_customer[1],
            "phone": updated_customer[2]
        }
    except sqlite3.IntegrityError as e:
        close_db(connection)
        raise HTTPException(status_code=400, detail=f"Error updating customer: Phone number must be unique")
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    try:
        (connection, cursor) = open_db()
        # Check if customer exists
        existing_customer = cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
        if not existing_customer:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Customer not found")
        # Check if customer has orders
        orders = cursor.execute("SELECT id FROM orders WHERE cust_id = ?;", (customer_id,)).fetchall()
        if orders:
            close_db(connection)
            raise HTTPException(status_code=400, detail="Cannot delete customer with existing orders")
        cursor.execute("DELETE FROM customers WHERE id = ?;", (customer_id,))
        close_db(connection)
        return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error deleting customer: {str(e)}")

# Items
@app.post("/items")
def create_item(item: Item):
    try:
        (connection, cursor) = open_db()
        cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);", (item.name, item.price))
        item_id = cursor.lastrowid
        created_item = cursor.execute("SELECT * FROM items WHERE id = ?;", (item_id,)).fetchone()
        close_db(connection)
        return {
            "id": created_item[0],
            "name": created_item[1],
            "price": created_item[2]
        }
    except sqlite3.IntegrityError as e:
        close_db(connection)
        raise HTTPException(status_code=400, detail=f"Error creating item: Item name must be unique")
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")

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
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    if item.id is not None and int(item.id) != int(item_id):
        raise HTTPException(status_code=400, detail="Item ID in path and body must match")
    try:
        (connection, cursor) = open_db()
        # Check if item exists
        existing_item = cursor.execute("SELECT * FROM items WHERE id = ?;", (item_id,)).fetchone()
        if not existing_item:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Item not found")
        cursor.execute("UPDATE items SET name = ?, price = ? WHERE id = ?;", (item.name, item.price, item_id))
        updated_item = cursor.execute("SELECT * FROM items WHERE id = ?;", (item_id,)).fetchone()
        close_db(connection)
        return {
            "id": updated_item[0],
            "name": updated_item[1],
            "price": updated_item[2]
        }
    except sqlite3.IntegrityError as e:
        close_db(connection)
        raise HTTPException(status_code=400, detail=f"Error updating item: Item name must be unique")
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    try:
        (connection, cursor) = open_db()
        # Check if item exists
        existing_item = cursor.execute("SELECT * FROM items WHERE id = ?;", (item_id,)).fetchone()
        if not existing_item:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Item not found")
        # Check if item is used in any orders
        orders = cursor.execute("SELECT order_id FROM item_list WHERE item_id = ?;", (item_id,)).fetchall()
        if orders:
            close_db(connection)
            raise HTTPException(status_code=400, detail="Cannot delete item that is used in existing orders")
        cursor.execute("DELETE FROM items WHERE id = ?;", (item_id,))
        close_db(connection)
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")

# Orders
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
    if not order:
        close_db(connection)
        raise HTTPException(status_code=404, detail="Order not found")
    order = await format_order_rows_to_dict(cursor, [order])
    close_db(connection)
    if len(order) > 0:
        return order[0]
    else:
        raise HTTPException(status_code=404, detail="Order not found")

@app.put("/orders/{order_id}")
async def update_order(order_id: int, order: Order):
    if order.id is not None and int(order.id) != int(order_id):
        raise HTTPException(status_code=400, detail="Order ID in path and body must match")
    try:
        (connection, cursor) = open_db()
        # Check if order exists
        existing_order = cursor.execute("SELECT * FROM orders WHERE id = ?;", (order_id,)).fetchone()
        if not existing_order:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate that the customer exists
        customer = cursor.execute("SELECT id FROM customers WHERE id = ?;", (order.cust_id,)).fetchone()
        if not customer:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Customer not found")

        # Validate that order has at least one item
        if not order.items:
            close_db(connection)
            raise HTTPException(
                status_code=400,
                detail="Order must contain at least one item."
            )

        # Validate all item IDs exist
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
            close_db(connection)
            raise HTTPException(
                status_code=404,
                detail=f"Invalid item IDs: {invalid_item_ids}"
            )

        # Update the order
        cursor.execute("UPDATE orders SET cust_id = ?, notes = ? WHERE id = ?;",
                      (order.cust_id, order.notes, order_id))

        # Delete existing item_list entries for this order
        cursor.execute("DELETE FROM item_list WHERE order_id = ?;", (order_id,))

        # Insert new items into item_list
        for item_id in order.items:
            cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);",
                          (order_id, item_id))

        # Fetch the updated order with customer details
        updated_order = cursor.execute("""
        SELECT orders.id, timestamp, name, phone, notes
        FROM orders, customers
        WHERE customers.id=cust_id AND orders.id=?;
        """, (order_id,)).fetchone()

        formatted_order = await format_order_rows_to_dict(cursor, [updated_order])
        close_db(connection)

        return formatted_order[0]
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    try:
        (connection, cursor) = open_db()
        # Check if order exists
        existing_order = cursor.execute("SELECT * FROM orders WHERE id = ?;", (order_id,)).fetchone()
        if not existing_order:
            close_db(connection)
            raise HTTPException(status_code=404, detail="Order not found")

        # Delete item_list entries first (due to foreign key constraint)
        cursor.execute("DELETE FROM item_list WHERE order_id = ?;", (order_id,))

        # Delete the order
        cursor.execute("DELETE FROM orders WHERE id = ?;", (order_id,))
        close_db(connection)
        return {"message": "Order deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        close_db(connection)
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")
