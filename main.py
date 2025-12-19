import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI()


def get_db_path():
    """Get the database path from environment variable, defaulting to 'db.sqlite'."""
    return os.getenv("DB_PATH", "db.sqlite")


# Pydantic models
class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Enforce phone numbers in the format 111-111-1111 (US-style).
        """
        if not re.fullmatch(r"\d{3}-\d{3}-\d{4}", v):
            raise ValueError("Phone number must be entered in the following format: 111-111-1111")
        return v


class Item(BaseModel):
    id: Optional[int] = None
    name: str
    price: float

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """
        Ensure price is provided as an integer or a dot-separated float.
        If an integer is provided, it is stored as a float with .00.
        """
        # Pydantic will already coerce JSON numbers to float; here we guard against
        # obviously bad formats like comma-separated strings, etc.
        # Accept ints and floats, but reject strings that are not plain numbers.
        if isinstance(v, (int, float)):
            return float(v)

        # If it's a string, only allow simple numeric representations using '.' as decimal separator
        if isinstance(v, str):
            if not re.fullmatch(r"\d+(\.\d+)?", v):
                raise ValueError(
                    "Price must be a number using a dot as the decimal separator, "
                    "for example 10 or 10.99"
                )
            return float(v)

        raise ValueError(
            "Price must be an integer or a float using a dot as the decimal separator, for example 10 or 10.99"
        )


class Order(BaseModel):
    id: Optional[int] = None
    cust_id: int
    notes: Optional[str] = None
    timestamp: Optional[int] = None
    # Use default_factory to avoid mutable default list being shared between instances
    items: List[int] = Field(default_factory=list)


# Database utilities
@contextmanager
def db_connection():
    """
    Context manager that opens an SQLite connection with foreign key enforcement,
    yields (connection, cursor), and handles commit/rollback and close.
    """
    connection = sqlite3.connect(get_db_path())
    # Ensure SQLite actually enforces foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON;")
    cursor = connection.cursor()
    try:
        yield connection, cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_order_items(cursor, order_id: int):
    items = cursor.execute(
        """
        SELECT i.name, i.price
        FROM items AS i
        JOIN item_list AS il ON i.id = il.item_id
        WHERE il.order_id = ?;
        """,
        (order_id,),
    ).fetchall()
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


def format_order_rows_to_dict(cursor, rows):
    formatted_rows = []
    for row in rows:
        formatted_rows.append({
            "id": row[0],
            "timestamp": row[1],
            "name": row[2],
            "phone": row[3],
            "notes": row[4],
            "items": get_order_items(cursor, row[0])
        })
    return formatted_rows


# API endpoints
# Customers
@app.post("/customers")
def create_customer(customer: Customer):
    try:
        with db_connection() as (connection, cursor):
            cursor.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?);",
                (customer.name, customer.phone),
            )
            customer_id = cursor.lastrowid
            created_customer = cursor.execute(
                "SELECT * FROM customers WHERE id = ?;", (customer_id,)
            ).fetchone()
            return {
                "id": created_customer[0],
                "name": created_customer[1],
                "phone": created_customer[2],
            }
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error creating customer: Customer with this phone number already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    with db_connection() as (connection, cursor):
        row = cursor.execute(
            "SELECT * FROM customers WHERE id = ?;", (customer_id,)
        ).fetchone()
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
        with db_connection() as (connection, cursor):
            # Check if customer exists
            existing_customer = cursor.execute(
                "SELECT * FROM customers WHERE id = ?;", (customer_id,)
            ).fetchone()
            if not existing_customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            cursor.execute(
                "UPDATE customers SET name = ?, phone = ? WHERE id = ?;",
                (customer.name, customer.phone, customer_id),
            )
            updated_customer = cursor.execute(
                "SELECT * FROM customers WHERE id = ?;", (customer_id,)
            ).fetchone()
            return {
                "id": updated_customer[0],
                "name": updated_customer[1],
                "phone": updated_customer[2],
            }
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error updating customer: Phone number must be unique")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    try:
        with db_connection() as (connection, cursor):
            # Check if customer exists
            existing_customer = cursor.execute(
                "SELECT * FROM customers WHERE id = ?;", (customer_id,)
            ).fetchone()
            if not existing_customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            # Check if customer has orders
            orders = cursor.execute(
                "SELECT 1 FROM orders WHERE cust_id = ? LIMIT 1;", (customer_id,)
            ).fetchone()
            if orders:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete customer with existing orders",
                )
            cursor.execute("DELETE FROM customers WHERE id = ?;", (customer_id,))
            return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting customer: {str(e)}")


# Items
@app.post("/items")
def create_item(item: Item):
    try:
        with db_connection() as (connection, cursor):
            cursor.execute(
                "INSERT INTO items (name, price) VALUES (?, ?);",
                (item.name, item.price),
            )
            item_id = cursor.lastrowid
            created_item = cursor.execute(
                "SELECT * FROM items WHERE id = ?;", (item_id,)
            ).fetchone()
            return {
                "id": created_item[0],
                "name": created_item[1],
                "price": created_item[2],
            }
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error creating item: Item name must be unique")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@app.get("/items/{item_id}")
def get_item(item_id: int):
    with db_connection() as (connection, cursor):
        row = cursor.execute(
            "SELECT * FROM items WHERE id = ?;", (item_id,)
        ).fetchone()
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
        with db_connection() as (connection, cursor):
            # Check if item exists
            existing_item = cursor.execute(
                "SELECT * FROM items WHERE id = ?;", (item_id,)
            ).fetchone()
            if not existing_item:
                raise HTTPException(status_code=404, detail="Item not found")
            cursor.execute(
                "UPDATE items SET name = ?, price = ? WHERE id = ?;",
                (item.name, item.price, item_id),
            )
            updated_item = cursor.execute(
                "SELECT * FROM items WHERE id = ?;", (item_id,)
            ).fetchone()
            return {
                "id": updated_item[0],
                "name": updated_item[1],
                "price": updated_item[2],
            }
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error updating item: Item name must be unique")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    try:
        with db_connection() as (connection, cursor):
            # Check if item exists
            existing_item = cursor.execute(
                "SELECT * FROM items WHERE id = ?;", (item_id,)
            ).fetchone()
            if not existing_item:
                raise HTTPException(status_code=404, detail="Item not found")
            # Check if item is used in any orders
            orders = cursor.execute(
                "SELECT 1 FROM item_list WHERE item_id = ? LIMIT 1;", (item_id,)
            ).fetchone()
            if orders:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete item that is used in existing orders",
                )
            cursor.execute("DELETE FROM items WHERE id = ?;", (item_id,))
            return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


# Orders
@app.post("/orders")
def create_order(order: Order):
    try:
        with db_connection() as (connection, cursor):
            # Validate that the customer exists
            customer = cursor.execute(
                "SELECT id FROM customers WHERE id = ?;", (order.cust_id,)
            ).fetchone()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Validate that order has at least one item
            if not order.items:
                raise HTTPException(
                    status_code=400,
                    detail="Order must contain at least one item.",
                )

            # Validate all item IDs exist before inserting anything
            item_ids = order.items
            placeholders = ",".join(["?"] * len(item_ids))
            existing_items = cursor.execute(
                f"SELECT id FROM items WHERE id IN ({placeholders});",
                item_ids,
            ).fetchall()
            existing_item_ids = {row[0] for row in existing_items}

            # Check for invalid item IDs
            invalid_item_ids = [
                item_id for item_id in item_ids if item_id not in existing_item_ids
            ]
            if invalid_item_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"Invalid item IDs: {invalid_item_ids}",
                )

            # Insert the order
            cursor.execute(
                "INSERT INTO orders (cust_id, notes) VALUES (?, ?);",
                (order.cust_id, order.notes),
            )
            order_id = cursor.lastrowid

            # Insert items into item_list
            for item_id in order.items:
                cursor.execute(
                    "INSERT INTO item_list (order_id, item_id) VALUES (?, ?);",
                    (order_id, item_id),
                )

            # Fetch the created order with customer details
            created_order = cursor.execute(
                """
        SELECT o.id, o.timestamp, c.name, c.phone, o.notes
        FROM orders AS o
        JOIN customers AS c ON c.id = o.cust_id
        WHERE o.id = ?;
        """,
                (order_id,),
            ).fetchone()

            formatted_order = format_order_rows_to_dict(cursor, [created_order])

            return formatted_order[0]
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with db_connection() as (connection, cursor):
        order = cursor.execute(
            """
    SELECT o.id, o.timestamp, c.name, c.phone, o.notes
    FROM orders AS o
    JOIN customers AS c ON c.id = o.cust_id
    WHERE o.id = ?;
    """,
            (order_id,),
        ).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order = format_order_rows_to_dict(cursor, [order])
    if len(order) > 0:
        return order[0]
    else:
        raise HTTPException(status_code=404, detail="Order not found")


@app.put("/orders/{order_id}")
def update_order(order_id: int, order: Order):
    if order.id is not None and int(order.id) != int(order_id):
        raise HTTPException(status_code=400, detail="Order ID in path and body must match")
    try:
        with db_connection() as (connection, cursor):
            # Check if order exists
            existing_order = cursor.execute(
                "SELECT * FROM orders WHERE id = ?;", (order_id,)
            ).fetchone()
            if not existing_order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Validate that the customer exists
            customer = cursor.execute(
                "SELECT id FROM customers WHERE id = ?;", (order.cust_id,)
            ).fetchone()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Validate that order has at least one item
            if not order.items:
                raise HTTPException(
                    status_code=400,
                    detail="Order must contain at least one item.",
                )

            # Validate all item IDs exist
            item_ids = order.items
            placeholders = ",".join(["?"] * len(item_ids))
            existing_items = cursor.execute(
                f"SELECT id FROM items WHERE id IN ({placeholders});",
                item_ids,
            ).fetchall()
            existing_item_ids = {row[0] for row in existing_items}

            # Check for invalid item IDs
            invalid_item_ids = [
                item_id for item_id in item_ids if item_id not in existing_item_ids
            ]
            if invalid_item_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"Invalid item IDs: {invalid_item_ids}",
                )

            # Update the order
            cursor.execute(
                "UPDATE orders SET cust_id = ?, notes = ? WHERE id = ?;",
                (order.cust_id, order.notes, order_id),
            )

            # Delete existing item_list entries for this order
            cursor.execute("DELETE FROM item_list WHERE order_id = ?;", (order_id,))

            # Insert new items into item_list
            for item_id in order.items:
                cursor.execute(
                    "INSERT INTO item_list (order_id, item_id) VALUES (?, ?);",
                    (order_id, item_id),
                )

            # Fetch the updated order with customer details
            updated_order = cursor.execute(
                """
        SELECT o.id, o.timestamp, c.name, c.phone, o.notes
        FROM orders AS o
        JOIN customers AS c ON c.id = o.cust_id
        WHERE o.id = ?;
        """,
                (order_id,),
            ).fetchone()

            formatted_order = format_order_rows_to_dict(cursor, [updated_order])

            return formatted_order[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")


@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    try:
        with db_connection() as (connection, cursor):
            # Check if order exists
            existing_order = cursor.execute(
                "SELECT * FROM orders WHERE id = ?;", (order_id,)
            ).fetchone()
            if not existing_order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Delete item_list entries first (due to foreign key constraint)
            cursor.execute("DELETE FROM item_list WHERE order_id = ?;", (order_id,))

            # Delete the order
            cursor.execute("DELETE FROM orders WHERE id = ?;", (order_id,))
            return {"message": "Order deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")
