from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('encode/', views.encode_view, name='encode'),
    path('decode/', views.decode_view, name='decode'),
]
