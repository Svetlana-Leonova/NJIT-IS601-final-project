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

def test_create_order_no_items_returns_400(client):
    """Test that creating an order with no items returns 400 Bad Request."""
    cust_resp = client.post("/customers", json={"name": "Order User 2", "phone": "555-555-5556"})
    assert cust_resp.status_code == 200
    customer_id = cust_resp.json()["id"]
    order_payload = {"cust_id": customer_id, "notes": "Bad order", "items": []}
    resp = client.post("/orders", json=order_payload)
    assert resp.status_code == 400
    assert "Order must contain at least one item." in resp.json()["detail"]

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

def test_create_order_invalid_customer_id(client):
    """Test that creating an order with a non-existent customer ID returns 404 Not Found."""
    order_payload = {"cust_id": 999999, "notes": "Bad order", "items": [1]}
    resp = client.post("/orders", json=order_payload)
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]

def test_get_order_happy_path(client):
    """Test that fetching an order returns 200 OK."""
    resp = client.get("/orders/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] is not None
    assert data["phone"] is not None
    assert len(data["items"]) > 0

def test_get_non_existent_order_returns_404(client):
    """Test that fetching a non-existent order returns 404 Not Found."""
    resp = client.get("/orders/999999")
    assert resp.status_code == 404
    assert "Order not found" in resp.json()["detail"]

def test_get_order_invalid_input_returns_422(client):
    """Test that fetching an order with an invalid input returns 400 Bad Request."""
    resp = client.get("/orders/invalid")
    assert resp.status_code == 422

def test_update_order_happy_path(client):
    """Test that updating an order returns 200 OK."""
    item_id = 1
    resp = client.put("/orders/1", json={"cust_id": 1, "notes": "Updated order", "items": [item_id]})
    assert resp.status_code == 200
    data = resp.json()
    # Verify that the items are the same as the items in the order
    first_item_data = client.get(f"/items/{item_id}").json()
    assert data["items"][0]["name"] == first_item_data["name"]
    assert data["items"][0]["price"] == first_item_data["price"]

def test_update_non_existent_order_returns_404(client):
    """Test that updating a non-existent order returns 404 Not Found."""
    resp = client.put("/orders/999999", json={"cust_id": 1, "notes": "Updated order", "items": [1]})
    assert resp.status_code == 404
    assert "Order not found" in resp.json()["detail"]

def test_update_order_id_mismatch_returns_400(client):
    """Test that updating an order with an ID mismatch returns 400 Bad Request."""
    resp = client.put("/orders/1", json={"id": 2, "cust_id": 1, "notes": "Updated order", "items": [1]})
    assert resp.status_code == 400
    assert "Order ID in path and body must match" in resp.json()["detail"]

def test_update_order_invalid_item_id(client):
    """Test that updating an order with an invalid item ID returns 404 Not Found."""
    resp = client.put("/orders/1", json={"cust_id": 1, "notes": "Updated order", "items": [999999]})
    assert resp.status_code == 404
    assert "Invalid item IDs" in resp.json()["detail"]

def test_update_order_no_items_returns_400(client):
    """Test that updating an order with no items returns 400 Bad Request."""
    resp = client.put("/orders/1", json={"cust_id": 1, "notes": "Updated order", "items": []})
    assert resp.status_code == 400
    assert "Order must contain at least one item." in resp.json()["detail"]

def test_update_order_invalid_customer_id(client):
    """Test that updating an order with a non-existent customer ID returns 404 Not Found."""
    resp = client.put("/orders/1", json={"cust_id": 999999, "notes": "Updated order", "items": [1]})
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]

def test_delete_order_happy_path(client):
    """Test that deleting an order returns 200 OK."""
    resp = client.delete("/orders/1")
    assert resp.status_code == 200
    assert "Order deleted successfully" in resp.json()["message"]

def test_delete_non_existent_order_returns_404(client):
    """Test that deleting a non-existent order returns 404 Not Found."""
    resp = client.delete("/orders/999999")
    assert resp.status_code == 404
    assert "Order not found" in resp.json()["detail"]
