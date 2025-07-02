# Routing in FastAPI

Routing is the process of determining how an application responds to a client request for a specific endpoint, which is defined by a URI (or path) and an HTTP method (e.g., GET, POST, PUT, DELETE). FastAPI makes it easy and intuitive to define routes for your API.

## Defining Routes with Decorators

In FastAPI, you define routes using decorators that correspond to HTTP methods. These decorators are applied to your path operation functions.

- `@app.get(path)`: For GET requests.
- `@app.post(path)`: For POST requests.
- `@app.put(path)`: For PUT requests.
- `@app.delete(path)`: For DELETE requests.
- `@app.patch(path)`: For PATCH requests.
- `@app.options(path)`: For OPTIONS requests.
- `@app.head(path)`: For HEAD requests.

*Example:*
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.post("/items/")
async def create_item(item_name: str):
    return {"name": item_name, "status": "created"}
```

## Path Parameters

You can declare path "parameters" or "variables" with the same syntax used by Python format strings. The value of the path parameter will be passed to your function as an argument.

*Example:*
```python
@app.get("/items/{item_id}")
async def read_item(item_id: int): # item_id is automatically converted to int
    return {"item_id": item_id}
```
In this case, `item_id` is a path parameter. If you navigate to `/items/5`, your function will receive `item_id=5`. FastAPI uses type hints for validation and serialization, so `item_id: int` ensures the path parameter is an integer.

## Query Parameters

When you declare function parameters for your path operation function that are not part of the path parameters, they are automatically interpreted as "query" parameters.

*Example:*
```python
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10): # skip and limit are query parameters
    fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]
    return fake_items_db[skip : skip + limit]
```
A request to `/items/?skip=0&limit=20` would call `read_items(skip=0, limit=20)`. Query parameters can have default values, and FastAPI will use them if they are not provided in the request. They can also be declared as optional by using `typing.Optional` or by providing a default value of `None`.

## Request Body

When you need to send data from a client (e.g., a browser) to your API, you send it as a "request body." A request body is data sent by the client to your API. A response body is the data your API sends to the client.

FastAPI uses **Pydantic models** to define, validate, and serialize request (and response) bodies. You declare the type of your request body parameter as a Pydantic model.

*Example:*
```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None # Python 3.10+ union type for Optional
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item): # 'item' is the request body
    return {"item_name": item.name, "price_with_tax": item.price + (item.tax or 0)}
```
FastAPI will:
1. Read the body of the request as JSON.
2. Convert the corresponding types (if needed).
3. Validate the data. If the data is invalid, it will return a clear error indicating what was wrong.
4. Give you the received data in the parameter `item`.

## Organizing Routes with `APIRouter`

For larger applications, it's beneficial to organize your routes into different files or modules. FastAPI provides `APIRouter` for this purpose. You can create an instance of `APIRouter` and define path operations on it, similar to how you do with a `FastAPI` app instance.

These routers are typically located in the `routers/` directory.

*Example (`routers/users.py`):*
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/users", # All routes in this router will start with /users
    tags=["users"],   # Group routes under "users" in OpenAPI docs
)

class User(BaseModel):
    username: str
    email: str

@router.post("/")
async def create_user(user: User):
    # Logic to create user
    return user

@router.get("/{user_id}")
async def get_user(user_id: int):
    # Logic to get user
    return {"user_id": user_id, "username": "fakeuser"}
```

### Including Routers in the Main App (`main.py`)

Once you have defined your `APIRouter` instances, you need to include them in your main FastAPI application, usually in `main.py`.

*Example (`main.py`):*
```python
from fastapi import FastAPI
from routers import users, items # Assuming you also have an items_router.py

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router) # Assuming items.router exists

@app.get("/")
async def read_root():
    return {"message": "Welcome to the main application"}
```

## Dependencies and Dependency Injection

FastAPI has a powerful but intuitive Dependency Injection system. Dependencies are functions (or classes) that can declare their own requirements (which can also be dependencies). FastAPI takes care of resolving these dependencies and "injecting" their results into your path operation functions.

Dependencies can be used for:
- Sharing database connections (e.g., `get_db` session).
- Enforcing authentication and authorization (e.g., `get_current_user`).
- Sharing common logic or data.

*Example:*
```python
from fastapi import Depends, FastAPI, HTTPException, status

app = FastAPI()

async def get_current_user(token: str | None = None): # A simple dependency
    if token != "fake-super-secret-token":
        raise HTTPException(status_code=401_UNAUTHORIZED, detail="Invalid token")
    return {"username": "testuser"}

@app.get("/users/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user
```
FastAPI will call `get_current_user` with the `token` query parameter (if provided) and pass its return value to `read_current_user` as `current_user`.

## Handling HTTP Exceptions

When an error occurs that should be reported to the client (e.g., item not found, invalid input, unauthorized access), you can raise an `HTTPException`. FastAPI will automatically convert this exception into an appropriate HTTP error response.

*Example:*
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```
If a client requests `/items/bar`, they will receive a 404 Not Found error with a JSON body `{"detail": "Item not found"}`.

## Request and Response Objects

FastAPI allows you to access the underlying Starlette `Request` and `Response` objects directly if you need more control or information.

- **Request Object:** You can declare a parameter of type `Request` in your path operation function. This gives you access to request headers, client host, cookies, etc.
  ```python
  from fastapi import FastAPI, Request

  app = FastAPI()

  @app.get("/ip")
  async def get_client_ip(request: Request):
      return {"client_host": request.client.host}
  ```

- **Response Object:** You can return a `starlette.responses.Response` (or its subclasses like `JSONResponse`, `HTMLResponse`, `RedirectResponse`) directly if you need to customize headers, status codes, or media types beyond what FastAPI provides by default. You can also declare a `Response` parameter in your path operation function to set cookies or headers on it.
  ```python
  from fastapi import FastAPI, Response
  from fastapi.responses import JSONResponse

  app = FastAPI()

  @app.get("/custom-response")
  async def custom_response_func(response: Response):
      response.headers["X-Custom-Header"] = "My custom header value"
      response.set_cookie(key="mycookie", value="cookie_value")
      return {"message": "Check headers and cookies!"}

  @app.get("/legacy/")
  async def get_legacy_data():
      data = {"message": "Legacy data"}
      return JSONResponse(content=data, status_code=200, headers={"X-Legacy": "true"})
  ```

## Status Codes

HTTP status codes are essential for clients to understand the outcome of their requests. FastAPI automatically returns sensible default status codes (e.g., 200 OK for successful GET, 201 Created for successful POST if no content is returned in the body, 422 Unprocessable Entity for validation errors).

You can explicitly set the status code for a response using the `status_code` parameter in the path operation decorator or when returning a `Response` object directly.

*Example:*
```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"name": name}
```
Common HTTP Status Codes:
- `200 OK`: Standard response for successful HTTP requests.
- `201 Created`: The request has been fulfilled, resulting in the creation of a new resource.
- `204 No Content`: The server successfully processed the request and is not returning any content.
- `400 Bad Request`: The server cannot or will not process the request due to an apparent client error.
- `401 Unauthorized`: Authentication is required and has failed or has not yet been provided.
- `403 Forbidden`: The server understood the request but refuses to authorize it.
- `404 Not Found`: The requested resource could not be found.
- `422 Unprocessable Entity`: The request was well-formed but was unable to be followed due to semantic errors (used by FastAPI for validation errors).
- `500 Internal Server Error`: A generic error message, given when an unexpected condition was encountered.

Understanding and utilizing these routing features effectively is key to building robust and maintainable APIs with FastAPI. Refer to the `routers/` directory for examples of how routes are structured in this project and `main.py` to see how they are integrated.
