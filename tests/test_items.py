def test_create_item_happy_path(client):
    """Test that an item can be created successfully."""
    payload = {"name": "Test Item", "price": 10.99}
    resp = client.post("/items", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99


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
    assert "Input should be a valid number" in resp.json()["detail"][0]["msg"]

def test_create_item_duplicate_name_returns_400(client):
    """Test that creating an item with a duplicate name returns 400 Bad Request."""
    payload = {"name": "Test Item", "price": 10.99}
    resp = client.post("/items", json=payload)
    assert resp.status_code == 200
    resp = client.post("/items", json=payload)
    assert resp.status_code == 400
    assert "Item name must be unique" in resp.json()["detail"]

def test_get_item_happy_path(client):
    """Test that fetching an item returns 200 OK."""
    resp = client.get("/items/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] is not None
    assert data["price"] is not None

def test_get_non_existent_item_returns_404(client):
    """Test that fetching a non-existent item returns 404 Not Found."""
    resp = client.get("/items/999999")
    assert resp.status_code == 404
    assert "Item not found" in resp.json()["detail"]

def test_update_item_happy_path(client):
    """Test that updating an item returns 200 OK."""
    resp = client.put("/items/1", json={"name": "Updated Item", "price": 11.99})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Item"
    assert data["price"] == 11.99

def test_update_non_existent_item_returns_404(client):
    """Test that updating a non-existent item returns 404 Not Found."""
    resp = client.put("/items/999999", json={"name": "Updated Item", "price": 11.99})
    assert resp.status_code == 404
    assert "Item not found" in resp.json()["detail"]

def test_update_item_id_mismatch_returns_400(client):
    """Test that updating an item with an ID mismatch returns 400 Bad Request."""
    resp = client.put("/items/1", json={"id": 2, "name": "Updated Item", "price": 11.99})
    assert resp.status_code == 400
    assert "Item ID in path and body must match" in resp.json()["detail"]

def test_update_item_invalid_price_format(client):
    """Test that updating an item with an invalid price format returns 422 validation error."""
    resp = client.put("/items/1", json={"name": "Updated Item", "price": "10,50"})
    assert resp.status_code == 422
    assert "Input should be a valid number" in resp.json()["detail"][0]["msg"]

def test_delete_item_happy_path(client):
    """Test that deleting an item returns 200 OK."""
    # Create an item
    resp = client.post("/items", json={"name": "Test Item", "price": 10.99})
    assert resp.status_code == 200
    item_id = resp.json()["id"]
    # Delete the item
    resp = client.delete(f"/items/{item_id}")
    assert resp.status_code == 200
    assert "Item deleted successfully" in resp.json()["message"]

def test_delete_non_existent_item_returns_404(client):
    """Test that deleting a non-existent item returns 404 Not Found."""
    resp = client.delete("/items/999999")
    assert resp.status_code == 404
    assert "Item not found" in resp.json()["detail"]

def test_delete_item_with_orders_returns_400(client):
    """Test that deleting an item with orders returns 400 Bad Request."""
    resp = client.delete("/items/1")
    assert resp.status_code == 400
    assert "Cannot delete item that is used in existing orders" in resp.json()["detail"]
