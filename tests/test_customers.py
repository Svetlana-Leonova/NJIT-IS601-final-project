def test_create_customer_success(client):
    """Test that a customer can be created successfully with valid phone format."""
    payload = {"name": "Test User", "phone": "123-456-7890"}
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test User"
    assert data["phone"] == "123-456-7890"


def test_create_customer_invalid_phone_format(client):
    """Test that creating a customer with invalid phone format returns 422 validation error."""
    payload = {"name": "Bad Phone", "phone": "1234567890"}
    resp = client.post("/customers", json=payload)
    # Pydantic validation error
    assert resp.status_code == 422

def test_create_customer_duplicate_phone_returns_400(client):
    """Test that creating a customer with a duplicate phone returns 400 Bad Request."""
    payload = {"name": "Duplicate User", "phone": "123-456-7890"}
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 200
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 400
    assert "Customer with this phone number already exists" in resp.json()["detail"]

def test_get_customer_happy_path(client):
    """Test that fetching a customer returns 200 OK."""
    resp = client.get("/customers/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] is not None
    assert data["phone"] is not None

def test_get_nonexistent_customer_returns_404(client):
    """Test that fetching a non-existent customer returns 404 Not Found."""
    resp = client.get("/customers/999999")
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]

def test_delete_customer_happy_path(client):
    """Test that deleting a customer that has no orders returns 200 OK."""
    # Create a customer
    resp = client.post("/customers", json={"name": "Delete User", "phone": "555-555-5555"})
    assert resp.status_code == 200
    customer_id = resp.json()["id"]
    # Delete the customer
    resp = client.delete(f"/customers/{customer_id}")
    assert resp.status_code == 200
    assert "Customer deleted successfully" in resp.json()["message"]
    # Verify the customer is deleted
    resp = client.get(f"/customers/{customer_id}")
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]

def test_delete_customer_with_orders_returns_400(client):
    """Test that deleting a customer with orders returns 400 Bad Request."""
    resp = client.delete("/customers/1")
    assert resp.status_code == 400
    assert "Cannot delete customer with existing orders" in resp.json()["detail"]

def test_update_customer_happy_path(client):
    """Test that updating a customer returns 200 OK."""
    customer_id = 1
    resp = client.put(f"/customers/{customer_id}", json={"id": customer_id, "name": "Updated User", "phone": "555-555-5555"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated User"
    assert data["phone"] == "555-555-5555"

def test_update_customer_id_mismatch_returns_400(client):
    """Test that updating a customer with an ID mismatch returns 400 Bad Request."""
    customer_id = 1
    resp = client.put(f"/customers/{customer_id}", json={"id": 2, "name": "Updated User", "phone": "555-555-5555"})
    assert resp.status_code == 400
    assert "Customer ID in path and body must match" in resp.json()["detail"]

def test_update_non_existent_customer_returns_404(client):
    """Test that updating a non-existent customer returns 404 Not Found."""
    customer_id = 999999
    resp = client.put(f"/customers/{customer_id}", json={"id": customer_id, "name": "Updated User", "phone": "555-555-5555"})
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]

def test_update_customer_invalid_phone_format_returns_422(client):
    """Test that updating a customer with an invalid phone format returns 422 Unprocessable Entity."""
    customer_id = 1
    resp = client.put(f"/customers/{customer_id}", json={"id": customer_id, "name": "Updated User", "phone": "1234567890"})
    assert resp.status_code == 422
    assert "Phone number must be entered in the following format: 111-111-1111" in resp.json()["detail"][0]["msg"]
