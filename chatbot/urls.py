from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('get-response/', views.get_response, name='get_response'),
    path('contact/', views.contact_view, name='contact'),
    path('clear-history/', views.clear_history, name='clear_history'),
]