from django.urls import path
from .views import EnfantListView, EnfantDetailView, EnfantCreateView, EnfantUpdateView, SuiviMedicalCreateView, SuiviScolaireCreateView, SuiviMedicalUpdateView, SuiviMedicalDeleteView, SuiviScolaireUpdateView, SuiviScolaireDeleteView, EnfantHistoryDetailView, EnfantHistoryListView, EnfantDeleteView, ReportView, DownloadExportView

app_name = 'enfants_gestion'

urlpatterns = [
    # Cette URL correspond à /enfants/
    path('', EnfantListView.as_view(), name='enfant_list'),
    # <int:pk> est un paramètre qui capture l'ID unique de l'enfant
    path('<int:pk>/', EnfantDetailView.as_view(), name='enfant_detail'),
    path('nouveau/', EnfantCreateView.as_view(), name='enfant_create'),
    path('<int:pk>/modifier/', EnfantUpdateView.as_view(), name='enfant_update'),
    path('<int:pk>/supprimer/', EnfantDeleteView.as_view(), name='enfant_delete'),

    path('enfant/<int:pk>/suivi-medical/ajouter/', SuiviMedicalCreateView.as_view(), name='suivi_medical_create'),
    path('enfant/<int:pk>/suivi-scolaire/ajouter/', SuiviScolaireCreateView.as_view(), name='suivi_scolaire_create'),

    path('suivi-medical/<int:pk>/modifier/', SuiviMedicalUpdateView.as_view(), name='suivi_medical_update'),
    path('suivi-medical/<int:pk>/supprimer/', SuiviMedicalDeleteView.as_view(), name='suivi_medical_delete'),

    path('suivi-scolaire/<int:pk>/modifier/', SuiviScolaireUpdateView.as_view(), name='suivi_scolaire_update'),
    path('suivi-scolaire/<int:pk>/supprimer/', SuiviScolaireDeleteView.as_view(), name='suivi_scolaire_delete'),
    path('historique/<int:pk>/', EnfantHistoryDetailView.as_view(), name='enfant_history_detail'),
    path('<int:pk>/historique/', EnfantHistoryListView.as_view(), name='enfant_history_list'),

    # ===================== IMPORT / EXPORT ===================
    # MODIFIEZ CETTE LIGNE
    path('export/', ReportView.as_view(), name='enfant_export'),
    # AJOUTEZ CETTE LIGNE
    path('export/download/', DownloadExportView.as_view(), name='enfant_download_export'),

    # Nous ajouterons les autres URLs (détail, création, etc.) ici plus tard
]