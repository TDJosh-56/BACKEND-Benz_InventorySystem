
# Dashboard API

A RESTful API for retrieving dashboard statistics and inventory information. It provides a centralized overview of ingredient stocks, stock alerts, inventory status distribution, and daily production totals.

## Base URL

All endpoints are relative to the URL where the Dashboard app is included in the project's `urls.py`.

```text
/api/
```

> All endpoints use a trailing slash. Authentication is not currently required.

## API Endpoint

| Method | Endpoint | Description |
|---|---|---|
| GET | `dashboard/` | Retrieve dashboard statistics and inventory overview |

## Dashboard Response Structure

### GET `dashboard/`

Retrieves the complete dashboard data, including summary statistics, stock alerts, stock levels, and stock overview.

### Example Request

```http
GET /api/dashboard/
```

### Example Response

```json
{
  "summary": {
    "total_ingredients": 25,
    "total_materials": 10,
    "low_stock_alerts": 4,
    "out_of_stock_alerts": 2,
    "production_today": 143
  },
  "stock_alerts": [
    {
      "ingredient_id": 1,
      "name": "Whole Milk",
      "current_stock": 2.5,
      "unit": "L",
      "status": "Low Stock"
    },
    {
      "ingredient_id": 2,
      "name": "Strawberry Syrup",
      "current_stock": 0.0,
      "unit": "L",
      "status": "Out of Stock"
    }
  ],
  "stock_levels": [
    {
      "ingredient_id": 1,
      "name": "Whole Milk",
      "current_stock": 2.5,
      "unit": "L",
      "status": "Low Stock"
    },
    {
      "ingredient_id": 3,
      "name": "Espresso Beans",
      "current_stock": 10.0,
      "unit": "kg",
      "status": "In Stock"
    }
  ],
  "stock_overview": {
    "in_stock": 19,
    "low_stock": 4,
    "out_of_stock": 2,
    "total": 25
  }
}
```

> The response above is an example. Actual values depend on the current inventory and production records.

## Response Fields

### 1. Summary

Provides the key statistics displayed in the dashboard's summary cards.

| Field | Type | Description |
|---|---|---|
| `total_ingredients` | Integer | Total number of active ingredients |
| `total_materials` | Integer | Total number of materials |
| `low_stock_alerts` | Integer | Number of ingredients with low stock |
| `out_of_stock_alerts` | Integer | Number of ingredients with no available stock |
| `production_today` | Integer | Total quantity of products produced today |

### 2. Stock Alerts

Contains ingredients that require inventory attention.

| Field | Type | Description |
|---|---|---|
| `ingredient_id` | Integer | Unique ingredient identifier |
| `name` | String | Ingredient name |
| `current_stock` | Float | Current available stock |
| `unit` | String | Ingredient stock measurement unit |
| `status` | String | Current stock status |

Only ingredients with the following statuses are included:

- `Low Stock`
- `Out of Stock`

### 3. Stock Levels

Contains the current stock information of all active ingredients.

| Field | Type | Description |
|---|---|---|
| `ingredient_id` | Integer | Unique ingredient identifier |
| `name` | String | Ingredient name |
| `current_stock` | Float | Current available stock |
| `unit` | String | Ingredient stock measurement unit |
| `status` | String | Current stock status |

This data can be used to display inventory charts, stock distribution, and ingredient usage information.

### 4. Stock Overview

Provides a summarized count of ingredients grouped by their stock status.

| Field | Type | Description |
|---|---|---|
| `in_stock` | Integer | Number of ingredients with sufficient stock |
| `low_stock` | Integer | Number of ingredients below their stock threshold |
| `out_of_stock` | Integer | Number of ingredients with zero available stock |
| `total` | Integer | Total number of active ingredients |

The stock overview can be used for dashboard charts and inventory distribution indicators.

## Stock Status Classification

Ingredients are categorized according to their current stock status.

| Status | Description |
|---|---|
| `In Stock` | Ingredient has sufficient available stock |
| `Low Stock` | Ingredient has reached its low-stock threshold |
| `Out of Stock` | Ingredient has no available stock |

> Stock status is determined by the inventory module and is reflected in the dashboard response.

## Production Statistics

The `production_today` field retrieves the total quantity of production records created on the current local date.

The calculation uses:

- Production records from the current date.
- The `quantity` field of each production record.
- The sum of all matching production quantities.

If no production records exist for the current date, the API returns `0`.

## Data Sources

The dashboard retrieves information from the following modules:

| Module | Model | Purpose |
|---|---|---|
| Inventory | `Ingredient` | Retrieves active ingredients and their stock information |
| Production | `ProductionRecord` | Retrieves daily production quantities |

## API Implementation

The dashboard follows a service-based structure to separate data processing from request handling.

### Project Structure

```text
dashboard/
├── __init__.py
├── serializers.py
├── services.py
├── views.py
└── urls.py
```

### Responsibilities

| File | Responsibility |
|---|---|
| `serializers.py` | Defines and validates the dashboard response structure |
| `services.py` | Retrieves inventory and production data and calculates dashboard statistics |
| `views.py` | Handles API requests and returns serialized responses |
| `urls.py` | Defines dashboard API routes |

## Frontend Integration Notes

When integrating the Dashboard API with the frontend:

1. Send a GET request to `dashboard/` when loading the dashboard.
2. Use `summary` to populate the dashboard statistic cards.
3. Use `stock_alerts` to display ingredients requiring attention.
4. Use `stock_levels` to display ingredient inventory information.
5. Use `stock_overview` to generate stock distribution charts.
6. Use `production_today` to display the total production for the current day.
7. Refresh the dashboard data after inventory or production operations to reflect updated values.

## HTTP Status Codes

| Status Code | Description |
|---|---|
| `200 OK` | Dashboard data successfully retrieved |
| `400 Bad Request` | Response data failed serializer validation |
| `500 Internal Server Error` | Unexpected server-side error |

---

**Technology:** Django REST Framework  
**Module:** Dashboard  
**Authentication:** None  
**HTTP Method:** GET  
**Response Format:** JSON
