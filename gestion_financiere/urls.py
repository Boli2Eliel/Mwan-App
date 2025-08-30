# gestion_financiere/urls.py
from django.urls import path
from .views import DonListView, DonCreateView, DonUpdateView, DonDeleteView, DepenseCreateView, DepenseUpdateView, DepenseListView, DepenseDeleteView, RapportFinancierView, get_comptes_for_site

app_name = 'gestion_financiere'

urlpatterns = [
    # URLs des Dons
    path('dons/', DonListView.as_view(), name='don_list'),
    path('dons/ajouter/', DonCreateView.as_view(), name='don_create'),
    path('dons/<int:pk>/modifier/', DonUpdateView.as_view(), name='don_update'),
    path('dons/<int:pk>/supprimer/', DonDeleteView.as_view(), name='don_delete'),

    # URLs des Dépenses
    path('depenses/', DepenseListView.as_view(), name='depense_list'),
    path('depenses/ajouter/', DepenseCreateView.as_view(), name='depense_create'),
    path('depenses/<int:pk>/modifier/', DepenseUpdateView.as_view(), name='depense_update'),
    path('depenses/<int:pk>/supprimer/', DepenseDeleteView.as_view(), name='depense_delete'),

    path('rapports/', RapportFinancierView.as_view(), name='rapport_financier'),
    path('api/get-comptes/<int:site_id>/', get_comptes_for_site, name='api_get_comptes_for_site'),
]