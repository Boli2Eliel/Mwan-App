# gestion_financiere/resources.py

from import_export import resources
from .models import Don, Depense

class DonResource(resources.ModelResource):
    class Meta:
        model = Don
        fields = ('id', 'date_don', 'montant', 'donateur', 'compte__nom', 'site__nom', 'description')
        export_order = ('id', 'date_don', 'montant', 'donateur', 'compte__nom', 'site__nom', 'description')

class DepenseResource(resources.ModelResource):
    class Meta:
        model = Depense
        fields = ('id', 'date_depense', 'montant', 'categorie', 'compte__nom', 'site__nom', 'description')
        export_order = ('id', 'date_depense', 'montant', 'categorie', 'compte__nom', 'site__nom', 'description')