"""
URL configuration for dailybrief project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/feeds/', include('apps.feeds.urls')),
    path('api/core/', include('apps.core.urls')),
    path('api/newsapi/', include('apps.newsapi.urls')),
    path('api/digest/', include('apps.content.digest.urls')),
    path('', include('apps.articles.urls')),  # Articles URLs don't have prefix as they're under api/articles/
]
