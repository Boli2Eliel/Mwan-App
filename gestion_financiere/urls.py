from django.urls import path
from .views import (
    TransactionListView, EntreeCreateView, SortieCreateView, TransactionUpdateView, TransactionDeleteView,
    ParrainageListView, ParrainageDetailView, ParrainageCreateView, ParrainageUpdateView, ParrainageDeleteView,
    RapportFinancierView,
    get_comptes_for_site,
    TransactionExportView # <-- Assurez-vous que cet import est présent
)

app_name = 'gestion_financiere'

urlpatterns = [
    # URLs pour les Transactions
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/entree/ajouter/', EntreeCreateView.as_view(), name='entree_create'),
    path('transactions/sortie/ajouter/', SortieCreateView.as_view(), name='sortie_create'),
    path('transactions/<int:pk>/modifier/', TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/archiver/', TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # URL POUR L'EXPORT (LIGNE AJOUTÉE)
    path('transactions/exporter/', TransactionExportView.as_view(), name='transaction_export'),
    
    # URLs pour les Parrainages
    path('parrainages/', ParrainageListView.as_view(), name='parrainage_list'),
    path('parrainages/<int:pk>/', ParrainageDetailView.as_view(), name='parrainage_detail'),
    path('parrainages/ajouter/', ParrainageCreateView.as_view(), name='parrainage_create'),
    path('parrainages/<int:pk>/modifier/', ParrainageUpdateView.as_view(), name='parrainage_update'),
    path('parrainages/<int:pk>/supprimer/', ParrainageDeleteView.as_view(), name='parrainage_delete'),
    
    # URLs pour les Rapports et API
    path('rapports/', RapportFinancierView.as_view(), name='rapport_financier'),
    path('api/get-comptes/<int:site_id>/', get_comptes_for_site, name='api_get_comptes_for_site'),
]