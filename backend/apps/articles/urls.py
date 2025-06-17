from django.urls import path
from . import views

app_name = 'articles'
 
urlpatterns = [
    path('api/articles/feed', views.personalized_feed, name='personalized_feed'),
    path('api/articles/world', views.world_feed, name='world_feed'),
    path('api/articles/<str:public_id>', views.article_detail, name='article_detail'),
    path('api/articles/<str:public_id>/generate-summary', views.generate_article_summary, name='generate_article_summary'),
    path('api/articles/<str:public_id>/summary-status', views.article_summary_status, name='article_summary_status'),
] 