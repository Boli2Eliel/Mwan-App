# enfants_gestion/views_mixins.py
from sites_gestion.models import SiteOrphelinat

class SiteFilteredQuerysetMixin:
    """
    Mixin qui filtre un queryset pour :
    1. Ne montrer que les objets actifs (`is_active=True`).
    2. Appliquer les permissions granulaires par site.
    """
    site_filter_path = 'site' # Le chemin vers le champ 'site' depuis le modèle de la vue
    global_role_groups = ['Directeur', 'Gestionnaire', 'RH'] # Groupes avec une vue globale potentielle

    def get_queryset(self):
        user = self.request.user
        
        # On commence par ne prendre que les objets actifs du modèle de la vue.
        # Le modèle est défini dans la vue elle-même (ex: model = Enfant)
        queryset = self.model.objects.filter(is_active=True)

        # Définit si l'utilisateur a un rôle global
        is_global_role = user.groups.filter(name__in=self.global_role_groups).exists() and not user.sites.exists()
        
        # Le superuser et les rôles globaux voient tous les objets actifs
        if user.is_superuser or is_global_role:
            return queryset
        
        # Les autres utilisateurs sont filtrés par leurs sites assignés
        filter_kwargs = {
            f'{self.site_filter_path}__in': user.sites.all()
        }
        return queryset.filter(**filter_kwargs).distinct()