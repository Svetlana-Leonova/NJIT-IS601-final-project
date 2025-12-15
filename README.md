# Order Management System API

A RESTful API built with FastAPI for managing customers, items, and orders. This system provides full CRUD (Create, Read, Update, Delete) operations for all entities with proper validation and error handling.

## Features

- **Customer Management**: Create, read, update, and delete customers with unique phone number validation
- **Item Management**: Manage menu items with unique name validation and price tracking
- **Order Management**: Create and manage orders with customer associations and multiple items
- **Data Validation**: Comprehensive input validation using Pydantic models
- **Error Handling**: Proper HTTP status codes and error messages
- **SQLite Database**: Lightweight, file-based database for easy setup and portability
- **Sample Data**: Pre-configured sample data for testing and development

## Technology Stack

- **Python 3.x**: Programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLite**: Embedded relational database
- **Uvicorn**: ASGI server for running FastAPI applications

## Database Schema

The application uses four main tables:

1. **customers**: Stores customer information

   - `id` (INTEGER PRIMARY KEY)
   - `name` (CHAR(64) NOT NULL)
   - `phone` (CHAR(10) NOT NULL UNIQUE)

2. **items**: Stores menu items

   - `id` (INTEGER PRIMARY KEY)
   - `name` (CHAR(64) NOT NULL UNIQUE)
   - `price` (REAL NOT NULL)

3. **orders**: Stores order information

   - `id` (INTEGER PRIMARY KEY)
   - `timestamp` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
   - `cust_id` (INT NOT NULL)
   - `notes` (TEXT)

4. **item_list**: Junction table linking orders to items
   - `order_id` (NOT NULL, FOREIGN KEY to orders)
   - `item_id` (NOT NULL, FOREIGN KEY to items)
   - UNIQUE(order_id, item_id)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd NJIT-IS601-final-project
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install dependencies manually:

```bash
pip install fastapi uvicorn[standard]
```

### Optional: Create a Freeze File for Exact Reproducibility

After installing dependencies, you can create a freeze file that captures the exact versions of all installed packages (including transitive dependencies):

```bash
pip freeze > requirements-freeze.txt
```

This is useful for:

- **Exact reproducibility**: Ensures everyone gets the same package versions
- **Production deployments**: Prevents unexpected version conflicts
- **Debugging**: Helps identify if issues are version-related

The `requirements.txt` file includes only the direct dependencies, while `requirements-freeze.txt` (if created) includes all transitive dependencies with exact versions.

## Running the Application

### Step 1: Initialize the Database

Before running the application, you need to initialize the database with sample data:

```bash
python init_db.py
```

This will:

- Create the SQLite database file (`db.sqlite`)
- Create all necessary tables
- Populate the database with sample customers, items, and orders from the JSON files in the `data/` directory

### Step 2: Start the Server

Run the FastAPI application on port 8000. You can use any of the following methods:

**Option 1: Using FastAPI CLI (Recommended for development with auto-reload):**

This will automatically run on port 8000:

```bash
fastapi dev main.py
```

If you want to run the API on a different port (e.g. 8008):

```bash
fastapi dev main.py  --port 8008
```

**Option 2: Using Uvicorn directly:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Option 3: Using Python module:**

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

> **Note**: The `fastapi dev` command provides automatic reloading when code changes are detected, making it ideal for development. The `uvicorn` commands are more suitable for production deployments.

The API will be available at:

- **API Base URL**: `http://localhost:8000`
- **Interactive API Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative API Documentation (ReDoc)**: `http://localhost:8000/redoc`

## Example Usage

### Using cURL

```bash
# Create a customer
curl -X POST "http://localhost:8000/customers" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "phone": "5551234567"}'

# Get a customer
curl "http://localhost:8000/customers/1"

# Create an item
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "Masala Dosa", "price": 10.95}'

# Create an order
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{"cust_id": 1, "notes": "Extra spicy", "items": [1, 2]}'
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a customer
customer = requests.post(
    f"{BASE_URL}/customers",
    json={"name": "John Doe", "phone": "5551234567"}
)
print(customer.json())

# Create an order
order = requests.post(
    f"{BASE_URL}/orders",
    json={"cust_id": 1, "notes": "Extra spicy", "items": [1, 2]}
)
print(order.json())
```

## Error Handling

The API returns appropriate HTTP status codes:

- **200 OK**: Successful GET, PUT, DELETE operations
- **201 Created**: Successful POST operations (FastAPI default)
- **400 Bad Request**: Validation errors, constraint violations
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Unexpected server errors

Error responses include a `detail` field with a descriptive error message:

```json
{
	"detail": "Customer not found"
}
```

## Validation Rules

- **Customers**:

  - Phone numbers must be unique
  - Cannot delete customers with existing orders

- **Items**:

  - Item names must be unique
  - Cannot delete items that are used in existing orders

- **Orders**:
  - Must have at least one item
  - Customer ID must exist
  - All item IDs must exist

## Development

### Resetting the Database

To reset the database with fresh sample data:

```bash
# Delete the existing database
rm db.sqlite

# Reinitialize
python init_db.py
```

### Testing the API

You can test the API using:

1. **Swagger UI**: Visit `http://localhost:8000/docs` for an interactive API explorer
2. **ReDoc**: Visit `http://localhost:8000/redoc` for alternative documentation
3. **cURL**: Use command-line tools as shown in examples above
4. **Postman**: Import the API endpoints for testing
5. **Python requests**: Use the requests library as shown in exampless
