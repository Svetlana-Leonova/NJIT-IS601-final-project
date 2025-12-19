def test_create_item_price_int_coerced_to_float(client):
    """Test that integer prices are accepted and stored as floats (e.g., 10 becomes 10.0)."""
    payload = {"name": "Test Item Int Price", "price": 10}
    resp = client.post("/items", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Should be stored/returned as a float
    assert data["price"] == 10.0


def test_create_item_invalid_price_format(client):
    """Test that prices with comma separators (e.g., '10,50') are rejected with 422 error."""
    # Comma is not allowed; must be dot-separated
    payload = {"name": "Bad Price", "price": "10,50"}
    resp = client.post("/items", json=payload)
    assert resp.status_code == 422


def test_create_order_happy_path(client):
    """Test the complete order creation flow: create customer, item, then order linking them."""
    # Create a customer and item first, then create an order referencing them
    cust_resp = client.post("/customers", json={"name": "Order User", "phone": "555-555-5555"})
    assert cust_resp.status_code == 200
    customer_id = cust_resp.json()["id"]

    item_resp = client.post("/items", json={"name": "Order Item", "price": 12.5})
    assert item_resp.status_code == 200
    item_id = item_resp.json()["id"]

    order_payload = {"cust_id": customer_id, "notes": "Test order", "items": [item_id]}
    order_resp = client.post("/orders", json=order_payload)
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    assert order_data["name"] == "Order User"
    assert order_data["phone"] == "555-555-5555"
    assert len(order_data["items"]) == 1


def test_create_order_invalid_item_id(client):
    """Test that creating an order with a non-existent item ID returns 404 with helpful error."""
    cust_resp = client.post("/customers", json={"name": "Order User 2", "phone": "555-555-5556"})
    assert cust_resp.status_code == 200
    customer_id = cust_resp.json()["id"]

    # Use an obviously invalid item id
    order_payload = {"cust_id": customer_id, "notes": "Bad order", "items": [999999]}
    resp = client.post("/orders", json=order_payload)
    assert resp.status_code == 404
    assert "Invalid item IDs" in resp.json()["detail"]

