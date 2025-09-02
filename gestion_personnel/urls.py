# gestion_personnel/urls.py
from django.urls import path
from .views import (
    EmployeListView, EmployeCreateView, EmployeUpdateView, EmployeDetailView, EmployeDeleteView
)

app_name = 'gestion_personnel'

urlpatterns = [
    path('', EmployeListView.as_view(), name='employe_list'),
    path('ajouter/', EmployeCreateView.as_view(), name='employe_create'),
    path('<int:pk>/', EmployeDetailView.as_view(), name='employe_detail'),
    path('<int:pk>/modifier/', EmployeUpdateView.as_view(), name='employe_update'),
    path('<int:pk>/archiver/', EmployeDeleteView.as_view(), name='employe_delete'),
]