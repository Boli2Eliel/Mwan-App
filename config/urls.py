from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('dashboard.urls')),

    path('finances/', include('gestion_financiere.urls')),

    # On dit à Django : "Toutes les URLs commençant par 'enfants/'
    # doivent être gérées par le fichier urls.py de l'app enfants_gestion"
    path('enfants/', include('enfants_gestion.urls')),

    path('personnel/', include('gestion_personnel.urls')),

    path('connexion/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('deconnexion/', LogoutView.as_view(), name='logout'),

    # Vous pouvez ajouter une page d'accueil simple ici si vous le souhaitez
    # path('', MaVueDeTableauDeBord.as_view(), name='dashboard'),
]

# Permet de servir les fichiers media (photos uploadées) en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)