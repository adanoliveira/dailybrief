"""
Example view using the standardized API approach.
This demonstrates the recommended pattern for implementing API endpoints.
"""
from .api_utils import api_view, create_response, create_error_response, parse_request_body

# Simple example without database access
@api_view(allowed_methods=["GET"], authenticate=False)
def hello_world(request):
    """
    Simple example view that returns a hello world message.
    
    This shows how to use the api_view decorator and response utilities
    without database access.
    """
    # Return a simple greeting
    data = {
        'message': 'Hello, world!',
        'status': 'ok',
        'version': '1.0'
    }
    
    # You can add query parameters, for example:
    name = request.GET.get('name')
    if name:
        data['message'] = f'Hello, {name}!'
    
    # Return the response using the utility function
    return create_response(data)

@api_view(allowed_methods=["POST"], authenticate=False)
def echo_data(request):
    """
    Example view that echoes back the posted data.
    
    This shows how to use the api_view decorator, request body parsing,
    and response utilities.
    """
    # Parse the request body
    data, error = parse_request_body(request)
    if error:
        return error
    
    # Validate required fields
    if not data:
        return create_error_response("Request body is empty", status=400)
    
    # Return the received data
    return create_response({
        'message': 'Data received successfully',
        'received': data,
        'success': True
    })

# More complex example (commented out since it depends on models from the feeds app)
"""
# To use this example, you would need to import models from the feeds app:
from apps.feeds.models import Topic, Region, Language, Publication

@api_view(allowed_methods=["GET"])
def get_reference_data_example(request):
    '''
    Example view to get reference data using the standardized pattern.
    
    This shows how to use the api_view decorator and response utilities
    with database access.
    '''
    # Get data from the database
    topics = list(Topic.objects.all().order_by('name').values('id', 'name', 'slug'))
    regions = list(Region.objects.all().order_by('name').values('id', 'code', 'name'))
    languages = list(Language.objects.all().order_by('name').values('id', 'iso_code', 'name'))
    
    # For publications, we need to handle the M2M relationships carefully
    publications_list = []
    publications = Publication.objects.all().order_by('-authority')[:20]
    
    for pub in publications:
        pub_data = {
            'id': pub.id,
            'name': pub.name,
            'website_url': pub.website_url,
            'logo_url': pub.logo_url if pub.logo_url else '',
            'description': pub.description if pub.description else '',
            'authority': float(pub.authority) if pub.authority else 1.0,
            'news_api_id': pub.news_api_id if pub.news_api_id else '',
            # Get related IDs
            'topic_ids': list(pub.topics.values_list('id', flat=True)),
            'region_ids': list(pub.regions.values_list('id', flat=True)),
            'language_ids': list(pub.languages.values_list('id', flat=True)),
        }
        publications_list.append(pub_data)
    
    # Assemble the response
    data = {
        'topics': topics,
        'regions': regions,
        'languages': languages,
        'publications': publications_list
    }
    
    # Return the response using the utility function
    return create_response(data)
""" 