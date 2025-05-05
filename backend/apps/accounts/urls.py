from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('sync/', csrf_exempt(views.sync_user), name='sync_user'),
    path('user/status/', csrf_exempt(views.check_user_status), name='user_status'),
    path('onboarding/save/', views.save_onboarding, name='save_onboarding'),
    path('preferences/', csrf_exempt(lambda request: 
        views.get_preferences_direct(request) if request.method == 'GET' 
        else views.save_preferences_direct(request)
    ), name='user_preferences'),
] 