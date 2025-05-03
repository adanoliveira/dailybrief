# Core App - API Utilities

This app provides utilities for standardized API responses using Django's `JsonResponse` instead of Django REST Framework.

## Why Direct Django Instead of DRF?

We encountered recursion issues with DRF when dealing with complex data structures and nested relationships. The direct Django approach is:

- More lightweight
- Avoids recursion issues with complex model relationships
- Gives more explicit control over response formatting
- Simplifies authentication and request handling

## Usage

### API View Decorator

The `api_view` decorator provides standard functionality for API views:

```python
from apps.core.api_utils import api_view, create_response

@api_view(allowed_methods=["GET"], authenticate=True)
def my_api_view(request):
    # Your view logic here
    return create_response({"data": "value"})
```

The decorator handles:
- CORS preflight requests (OPTIONS)
- Method validation
- Authentication (if enabled)
- Error handling with logging

### Response Utilities

#### `create_response(data, status=200)`

Creates a standard JSON response with CORS headers:

```python
from apps.core.api_utils import create_response

def my_view(request):
    data = {"key": "value"}
    return create_response(data)
```

#### `create_error_response(message, status=400, error_code=None, details=None)`

Creates a standardized error response:

```python
from apps.core.api_utils import create_error_response

def my_view(request):
    if error_condition:
        return create_error_response("Something went wrong", status=400)
    # ...
```

#### `parse_request_body(request)`

Parses JSON request body with error handling:

```python
from apps.core.api_utils import parse_request_body, create_response

def my_view(request):
    data, error = parse_request_body(request)
    if error:
        return error
    
    # Use the parsed data
    return create_response({"received": data})
```

## Complete Example

See `apps/core/example_view.py` for a complete example of how to implement API views using this approach. The example includes:

- A simple GET endpoint that doesn't require authentication
- A POST endpoint that parses and echoes request data
- A commented example showing database interaction 