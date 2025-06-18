# DailyBrief Utilities - DEPRECATED

⚠️ **This directory is largely deprecated.** Most utilities have been moved to more appropriate locations.

## Migration Status

### ✅ HTTP & API Utilities → `apps/core/api_utils.py`

The HTTP utilities (`http.py`) have been **consolidated** into the enhanced API utilities:

```python
# OLD (deprecated)
from utils.http import create_cors_response, handle_options_request

# NEW (recommended)
from apps.core.api_utils import create_response, create_error_response, api_view
```

**Benefits of the new location:**
- **Comprehensive**: Includes authentication, CORS, validation, pagination
- **Consistent**: Single decorator pattern for all endpoints  
- **Secure**: Built-in JWT authentication and staff requirements
- **Documented**: Complete examples and usage patterns

## Current Utilities

This directory now contains minimal shared utilities that don't fit elsewhere:

- `__init__.py`: Package marker

## For New Utilities

**Before adding utilities here**, consider these preferred locations:

1. **API-related**: Add to `apps/core/api_utils.py`
2. **App-specific**: Add to the relevant app's directory
3. **Model-related**: Add as model methods or managers
4. **Business logic**: Create dedicated service modules

## Migration Guide

If you're updating old code that imports from `utils/`:

```python
# Replace these old imports:
from utils.http import create_cors_response, handle_options_request

# With these new imports:
from apps.core.api_utils import (
    api_view, create_response, create_error_response,
    create_success_response, parse_request_body
)

# And use the new @api_view decorator:
@api_view(['GET', 'POST'])
def my_endpoint(request):
    user = request.user  # Auto-authenticated
    return create_response({'data': 'success'})
```

## Documentation

For complete API development guidelines, see:
- **API Standards**: `docs/api/api-standards.md`
- **Core Utilities**: `apps/core/README.md`
- **Examples**: `apps/core/example_view.py` 