# Core App - Enhanced API Utilities

This app provides the **unified API utilities** for DailyBrief, implementing our standardized approach to building secure, consistent, and maintainable API endpoints.

## 🎯 **Design Philosophy**

We use **Django's JsonResponse** with enhanced decorators instead of Django REST Framework to achieve:

- **🚫 No Recursion Issues**: Avoids DRF's complex serialization problems
- **⚡ Lightweight**: Minimal overhead, maximum performance  
- **🎛️ Explicit Control**: Full control over response formatting
- **🔒 Built-in Security**: Automatic CORS, authentication, and permissions
- **📝 Consistent Patterns**: Same approach across all endpoints

## 🏗️ **Core Architecture**

### **Enhanced @api_view Decorator**

The centerpiece of our API architecture provides comprehensive functionality:

```python
from apps.core.api_utils import api_view, create_response, create_error_response

@api_view(['GET', 'POST'], staff_required=True)
def my_admin_endpoint(request):
    """Comprehensive example with all features."""
    user = request.user  # Auto-authenticated + staff verified
    return create_response({'data': 'success'})
```

**Features:**
- ✅ **Automatic CORS**: OPTIONS preflight handling  
- ✅ **JWT Authentication**: NextAuth integration via `authenticate_request()`
- ✅ **HTTP Method Validation**: Only allow specified methods
- ✅ **Staff Requirements**: Optional staff-only endpoints
- ✅ **Exception Handling**: Comprehensive error logging + user-friendly responses
- ✅ **Standardized Responses**: Consistent JSON format across all endpoints

## 📝 **API Patterns & Examples**

### **1. Basic Authenticated Endpoint**

```python
@api_view(['GET'])
def get_user_data(request):
    """Get current user's data."""
    user = request.user  # Available after automatic authentication
    
    return create_response({
        'user_id': user.id,
        'email': user.email,
        'name': user.first_name
    })
```

### **2. Public Endpoint (No Authentication)**

```python
@api_view(['GET'], authenticate=False)
def public_data(request):
    """Public endpoint, no authentication required."""
    return create_response({
        'public_data': 'available to all',
        'timestamp': timezone.now().isoformat()
    })
```

### **3. Staff-Only Administrative Endpoint**

```python
@api_view(['POST'], staff_required=True)
def admin_action(request):
    """Staff-only administrative action."""
    user = request.user  # Guaranteed to be staff
    
    # Parse request body with validation
    data, error = parse_request_body(request)
    if error:
        return error
    
    # Perform admin action
    result = perform_admin_action(data)
    
    return create_success_response(
        {'action_id': result.id},
        message="Admin action completed successfully"
    )
```

### **4. Paginated List Endpoint**

```python
@api_view(['GET'])
def list_items(request):
    """Get paginated list of items."""
    user = request.user
    
    # Get query parameters with validation
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 100)
    filter_type = request.GET.get('type', 'all')
    
    # Get queryset
    queryset = Item.objects.filter(user=user)
    if filter_type != 'all':
        queryset = queryset.filter(item_type=filter_type)
    
    # Use built-in pagination utility
    result = paginate_response(queryset, page, page_size)
    
    return create_response(result)
```

### **5. Multi-Method Endpoint with Validation**

```python
@api_view(['GET', 'POST', 'PUT'])
def manage_preferences(request):
    """Get, create, or update user preferences."""
    user = request.user
    
    if request.method == 'GET':
        preferences = get_user_preferences(user)
        return create_response({'preferences': preferences})
    
    elif request.method in ['POST', 'PUT']:
        # Parse and validate request body
        data, error = parse_request_body(request)
        if error:
            return error
        
        # Validate required fields
        required_fields = ['topics', 'regions']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    f"Missing required field: {field}",
                    status=400,
                    error_code="MISSING_REQUIRED_FIELD",
                    details={"field": field, "required_fields": required_fields}
                )
        
        # Update preferences
        preferences = update_user_preferences(user, data)
        
        return create_success_response(
            {'preferences': preferences},
            message="Preferences updated successfully"
        )
```

## 🛠️ **Response Utilities**

### **Standard Success Responses**

```python
# Simple response
return create_response({'users': user_list})

# Success with message
return create_success_response(
    {'saved': True}, 
    message="Settings saved successfully"
)

# Paginated response
return create_response({
    'items': [...],
    'pagination': {
        'page': 1,
        'page_size': 10,
        'total_pages': 5,
        'total_count': 47,
        'has_next': True,
        'has_previous': False
    }
})
```

### **Standardized Error Responses**

```python
# Simple error
return create_error_response("User not found", status=404)

# Error with code and details
return create_error_response(
    "Validation failed",
    status=400,
    error_code="VALIDATION_ERROR",
    details={
        "field": "email",
        "issue": "Invalid format",
        "valid_formats": ["user@domain.com"]
    }
)

# Authentication error (automatic via @api_view)
# Returns 401 with standardized auth error message
```

### **Request Body Parsing**

```python
@api_view(['POST'])
def create_item(request):
    # Safe JSON parsing with error handling
    data, error = parse_request_body(request)
    if error:
        return error  # Returns 400 with JSON error details
    
    # Validate and use data
    if not data.get('name'):
        return create_error_response("Name is required")
    
    item = create_item_from_data(data)
    return create_response({'item_id': item.id})
```

## 📊 **Pagination Utility**

```python
@api_view(['GET'])
def list_articles(request):
    """Example of built-in pagination."""
    user = request.user
    
    # Get parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # Get queryset  
    articles = Article.objects.filter(user=user).order_by('-created_at')
    
    # Use pagination utility (max 100 items per page)
    result = paginate_response(articles, page, page_size, max_page_size=100)
    
    # Response includes both items and pagination metadata
    return create_response(result)
```

**Response Format:**
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 5,
    "total_count": 47,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

## 🔐 **Authentication & Security**

### **Automatic JWT Authentication**

The `@api_view` decorator automatically handles:

1. **Token Extraction**: Bearer token from Authorization header
2. **JWT Validation**: Format and signature verification  
3. **User Lookup**: Django user from token payload
4. **Request Enhancement**: Adds `request.user` for view access
5. **Error Responses**: 401 for invalid/missing tokens

```python
# Authentication happens automatically
@api_view(['GET'])  # authenticate=True by default
def protected_endpoint(request):
    user = request.user  # Always available and valid
    return create_response({'user_id': user.id})
```

### **Staff Permission Requirements**

```python
@api_view(['DELETE'], staff_required=True)
def delete_user(request, user_id):
    """Only staff can delete users."""
    user = request.user  # Guaranteed to be staff
    
    # Perform staff-only action
    target_user = User.objects.get(id=user_id)
    target_user.delete()
    
    return create_success_response(
        {'deleted_user_id': user_id},
        message=f"User {target_user.email} deleted by {user.email}"
    )
```

## 🌐 **CORS & Cross-Origin Support**

All endpoints automatically include proper CORS headers:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With
Access-Control-Max-Age: 86400
```

**OPTIONS preflight requests** are handled automatically. No manual CORS configuration needed.

## 📋 **Response Format Standards**

### **Success Response Format**

```json
{
  "data": {...},
  "success": true,
  "message": "Optional success message"
}
```

### **Error Response Format**

```json
{
  "error": "Human readable error message",
  "success": false,
  "error_code": "OPTIONAL_ERROR_CODE",
  "details": {
    "additional": "context"
  }
}
```

### **HTTP Status Codes**

| Code | Usage | When to Use |
|------|-------|-------------|
| 200 | Success | Data retrieved/updated successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data, missing fields |
| 401 | Unauthorized | Missing/invalid authentication token |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method used |
| 500 | Internal Error | Server error, logged automatically |

## 🚀 **Usage Guidelines**

### **For New Endpoints**

1. **Always use `@api_view`** decorator
2. **Return `create_response()`** or `create_error_response()`
3. **Use `parse_request_body()`** for POST/PUT data
4. **Use `paginate_response()`** for list endpoints
5. **Include comprehensive docstrings**
6. **Follow error code conventions**

### **Migration from Legacy Patterns**

```python
# OLD (Manual Pattern)
@csrf_exempt
def old_view(request):
    if request.method == 'OPTIONS':
        return handle_options_request()
    
    authenticated, user, error = authenticate_request(request)
    if not authenticated:
        return get_auth_response(error)
    
    response = JsonResponse(data)
    response["Access-Control-Allow-Origin"] = "*"
    return response

# NEW (Standardized Pattern)
@api_view(['GET'])
def new_view(request):
    user = request.user  # Auto-authenticated
    return create_response(data)
```

## 🧪 **Testing Examples**

```python
from django.test import TestCase
from apps.core.api_utils import create_response

class MyEndpointTests(TestCase):
    def test_authenticated_access(self):
        """Test authenticated users can access endpoint."""
        response = self.client.get(
            '/api/my-endpoint/', 
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', True))
    
    def test_staff_only_endpoint(self):
        """Test staff-only endpoints reject regular users."""
        response = self.client.post(
            '/api/admin/action/',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'  # Not staff
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['error_code'], 'INSUFFICIENT_PERMISSIONS')
```

## 📁 **File Structure**

```
apps/core/
├── api_utils.py          # Enhanced API utilities
├── example_view.py       # Comprehensive examples
├── urls.py              # Example URL patterns
└── README.md            # This documentation
```

## 🔗 **Related Documentation**

- **API Standards**: `docs/api/api-standards.md` - Comprehensive API development standards
- **Authentication**: `docs/auth/authentication-architecture.md` - NextAuth + Django integration
- **Examples**: `apps/core/example_view.py` - Working code examples

---

**For comprehensive API standards and migration guidelines, see `docs/api/api-standards.md`** 