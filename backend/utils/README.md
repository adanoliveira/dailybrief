# DailyBrief Utilities

This directory contains shared utility functions and helpers used across multiple apps in the DailyBrief project.

## Overview

The utilities are organized by domain:

- `http.py`: Contains HTTP-related utilities, including CORS handling, response formatting, etc.

## Usage

### HTTP Utilities

```python
from utils.http import create_cors_response, handle_options_request, add_cors_headers

# Handle OPTIONS requests (CORS preflight)
if request.method == 'OPTIONS':
    return handle_options_request("GET, POST, OPTIONS")

# Create a success response with CORS headers
return create_cors_response({
    'data': 'Success!',
    'status': 'ok'
})

# Create an error response with CORS headers
return create_cors_response({}, status=400, error="Invalid request")

# Add CORS headers to an existing response
response = JsonResponse({'data': 'example'})
return add_cors_headers(response)
```

## Adding New Utilities

When adding new utility functions:

1. Place them in an appropriate domain-specific file (create a new one if needed)
2. Add proper type hints and docstrings
3. Keep functions focused on a single responsibility
4. Use consistent parameter and return types 