
# Recipe API

A RESTful API for managing recipes and their associated ingredients. This API supports recipe creation, retrieval, updating, deletion, archiving, categorization, and ingredient management.

## Base URL

All endpoints are relative to the URL where the Recipe app is included in the project's `urls.py`.

```text
/api/
```

> All endpoints use a trailing slash. Authentication is not currently required.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `recipes/` | Retrieve all recipes |
| POST | `recipes/` | Create a new recipe |
| GET | `recipes/<id>/` | Retrieve a specific recipe |
| PATCH | `recipes/<id>/` | Partially update a recipe |
| DELETE | `recipes/<id>/` | Delete a recipe |
| GET | `subcategories/` | Retrieve available subcategories |

## Recipe Data Structure

The following JSON represents the structure used for both recipe requests and responses.

### Example Response

```json
{
  "id": "12",
  "name": "Strawberry Frappe",
  "category": "Drink",
  "subcategory": "Frappe",
  "price": 120.0,
  "yieldAmount": 1,
  "yieldUnit": "cup/batch",
  "description": "Cold blended drink.",
  "isArchived": false,
  "imageUrl": "http://host/media/product/ab12cd34ef56.png",
  "ingredients": [
    {
      "ingredientId": "4",
      "ingredient_name": "Whole Milk",
      "category": "Ingredient",
      "quantity": 0.25,
      "unit": "L"
    }
  ]
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `id` | String | Unique recipe identifier |
| `name` | String | Recipe name |
| `category` | String | Recipe category (`Food` or `Drink`) |
| `subcategory` | String | Recipe subcategory |
| `price` | Number | Selling price |
| `yieldAmount` | Number | Recipe yield quantity |
| `yieldUnit` | String | Yield measurement unit |
| `description` | String | Recipe description |
| `isArchived` | Boolean | Whether the recipe is archived |
| `imageUrl` | String | Recipe image URL or Base64 image data |
| `ingredients` | Array | List of ingredients used in the recipe |

### Ingredient Object

| Field | Type | Description |
|---|---|---|
| `ingredientId` | String | ID of the existing inventory ingredient |
| `ingredient_name` | String | Ingredient name (response only) |
| `category` | String | Ingredient category (response only) |
| `quantity` | Number | Required ingredient quantity |
| `unit` | String | Measurement unit |

> When creating or updating a recipe, `id`, `ingredient_name`, and the ingredient `category` are ignored.

## Retrieving Recipes

### GET `recipes/`

Retrieves all recipes. Supports optional query parameters for filtering and searching.

### Query Parameters

| Parameter | Accepted Values | Description |
|---|---|---|
| `status` | `active`, `archived` | Filter recipes by archive status |
| `category` | `Food`, `Drink` | Filter by recipe category |
| `subcategory` | Text | Filter by subcategory name |
| `search` | Text | Search recipe names, descriptions, and ingredient names |

### Examples

Retrieve all recipes:

```http
GET /api/recipes/
```

Retrieve active recipes:

```http
GET /api/recipes/?status=active
```

Retrieve archived drinks:

```http
GET /api/recipes/?status=archived&category=Drink
```

Retrieve recipes under the Frappe subcategory:

```http
GET /api/recipes/?subcategory=Frappe
```

Search recipes:

```http
GET /api/recipes/?search=Strawberry
```

Combine multiple filters:

```http
GET /api/recipes/?status=active&category=Drink&subcategory=Frappe&search=Strawberry
```

## Creating a Recipe

### POST `recipes/`

Creates a new recipe.

### Example Request

```json
{
  "name": "Strawberry Frappe",
  "category": "Drink",
  "subcategory": "Frappe",
  "price": 120.0,
  "yieldAmount": 1,
  "yieldUnit": "cup/batch",
  "description": "Cold blended drink.",
  "imageUrl": "",
  "ingredients": [
    {
      "ingredientId": "4",
      "quantity": 0.25,
      "unit": "L"
    }
  ]
}
```

### Successful Response

**Status:** `201 Created`

Returns the newly created recipe, including its database-generated ID.

> Always use the returned database ID for subsequent operations. Do not use temporary frontend IDs such as `rec-...`.

## Retrieving a Single Recipe

### GET `recipes/<id>/`

Retrieves the details of a specific recipe.

Example:

```http
GET /api/recipes/12/
```

## Updating a Recipe

### PATCH `recipes/<id>/`

Updates one or more fields of an existing recipe.

Only the fields included in the request are updated. Omitted fields remain unchanged.

### Example Request

Update the recipe price:

```json
{
  "price": 135.0
}
```

Update the recipe subcategory:

```json
{
  "subcategory": "Milk-Based Frappe"
}
```

Archive a recipe:

```json
{
  "isArchived": true
}
```

Restore an archived recipe:

```json
{
  "isArchived": false
}
```

### Updating Ingredients

When the `ingredients` field is included in a PATCH request, the entire ingredient list is replaced.

Example:

```json
{
  "ingredients": [
    {
      "ingredientId": "4",
      "quantity": 0.3,
      "unit": "L"
    },
    {
      "ingredientId": "5",
      "quantity": 20,
      "unit": "g"
    }
  ]
}
```

> If `ingredients` is omitted, the existing ingredient list remains unchanged.

## Deleting a Recipe

### DELETE `recipes/<id>/`

Permanently deletes a recipe.

Example:

```http
DELETE /api/recipes/12/
```

**Successful Response:** `204 No Content`

The response body is empty.

## Retrieving Subcategories

### GET `subcategories/`

Retrieves all available recipe subcategories, ordered by most frequently used first.

### Example Response

```json
[
  {
    "id": 1,
    "name": "Frappe"
  },
  {
    "id": 2,
    "name": "Coffee"
  },
  {
    "id": 3,
    "name": "Pastry"
  }
]
```

### Subcategory Behavior

- Subcategories are created automatically when a new name is submitted.
- Existing subcategory names are matched case-insensitively.
- Subcategory names have a maximum length of 30 characters.
- Recipes without a subcategory return an empty string (`""`), never `null`.

## Image Handling

The `imageUrl` field supports Base64 image uploads, existing image URLs, and image removal.

| Input | Behavior |
|---|---|
| `data:image/png;base64,...` | Uploads or replaces the recipe image |
| Existing `http://...` URL | Keeps the current image |
| Field omitted | Keeps the current image |
| `""` | Removes the current image |

**Image Restrictions:**
- Maximum image size: 5 MB.
- Supported input: Base64-encoded image data URI.
- Recipes without an image return an empty string (`""`).

### Example Image Upload

```json
{
  "name": "Strawberry Frappe",
  "imageUrl": "data:image/png;base64,iVBORw0KGgo..."
}
```

## Validation Rules

### Recipe Validation

| Field | Validation |
|---|---|
| `name` | Required, maximum 50 characters |
| `category` | Must be `Food` or `Drink` (case-insensitive) |
| `subcategory` | Optional, maximum 30 characters |
| `price` | Must be greater than 0 |
| `yieldAmount` | Must be at least 1 |
| `yieldUnit` | Maximum 20 characters |
| `description` | Required, maximum 200 characters |
| `imageUrl` | Maximum 5 MB |
| `ingredients` | Must contain valid existing ingredients |

### Ingredient Validation

- Each ingredient can only appear once in a recipe.
- The referenced ingredient must exist and must not be deleted.
- Ingredient quantity must be greater than zero.
- Only the following measurement units are accepted:

| Unit | Measurement Type |
|---|---|
| `kg` | Weight |
| `g` | Weight |
| `L` | Volume |
| `mL` | Volume |
| `Pcs` | Piece / Count |

### Unit Compatibility

Ingredient units must be compatible with the ingredient's inventory stock unit.

| Stock Unit | Allowed Recipe Units |
|---|---|
| `kg` | `kg`, `g` |
| `g` | `kg`, `g` |
| `L` | `L`, `mL` |
| `mL` | `L`, `mL` |
| `Pcs` | `Pcs` |

Weight, volume, and piece measurements cannot be mixed.

## ID Handling

- Recipe IDs and ingredient IDs are returned as strings.
- Both string and numeric IDs are accepted in requests.
- After creating a recipe, always use the ID returned by the API.
- Frontend-generated temporary IDs must not be used for backend operations.

## Error Handling

The API returns HTTP `400 Bad Request` when request validation fails.

### Example Response

```json
{
  "price": [
    "Ensure this value is greater than or equal to 0.01."
  ]
}
```

Ingredient-related validation errors are returned under the `ingredients` field.

### Common HTTP Status Codes

| Status Code | Description |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | Recipe successfully created |
| `204 No Content` | Recipe successfully deleted |
| `400 Bad Request` | Validation error |
| `404 Not Found` | Recipe or requested resource does not exist |

## Frontend Integration Notes

When integrating the Recipe API with the frontend:

1. Fetch recipes using `GET recipes/`.
2. Use query parameters for searching, filtering, and displaying active or archived recipes.
3. Fetch available subcategories using `GET subcategories/`.
4. Use `POST recipes/` when creating a new recipe.
5. Use the returned database ID after successful creation.
6. Use `PATCH recipes/<id>/` when editing recipe information.
7. Remember that updating `ingredients` replaces the entire ingredient list.
8. Use `PATCH` to archive or restore recipes.
9. Use `DELETE` only when permanently removing a recipe.
10. Handle validation errors returned by the API and display them to the user.

---

**Technology:** Django REST Framework  
**Module:** Recipe Management  
**Authentication:** None  
**Response Format:** JSON
