from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/server_info', views.get_server_info, name='server_info'),
]