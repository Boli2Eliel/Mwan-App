# enfants_gestion/resources.py

from import_export import resources, fields
from .models import Enfant

class EnfantResource(resources.ModelResource):
    site_nom = fields.Field(attribute='site__nom', column_name="Site d'accueil")
    dernier_suivi_medical_date = fields.Field(column_name="Date du dernier suivi médical")
    dernier_suivi_medical_diag = fields.Field(column_name="Diagnostic du dernier suivi")
    derniere_annee_scolaire = fields.Field(column_name="Dernière année scolaire")
    derniere_classe = fields.Field(column_name="Dernière classe")

    class Meta:
        model = Enfant
        # ON AJOUTE NOS CHAMPS PERSONNALISÉS À LA LISTE BLANCHE 'fields'
        fields = (
            'id', 'nom', 'prenom', 'date_naissance', 'sexe', 'lieu_naissance', 
            'date_arrivee', 'statut', 'date_depart', 'is_active',
            'site_nom', 'dernier_suivi_medical_date', 'dernier_suivi_medical_diag',
            'derniere_annee_scolaire', 'derniere_classe'
        )
        export_order = fields # On peut simplement réutiliser la même liste pour l'ordre
    
        # Le dictionnaire widgets n'est plus nécessaire pour ce cas
    
    # Les fonctions "dehydrate" permettent de calculer la valeur de nos champs personnalisés
    def dehydrate_dernier_suivi_medical_date(self, enfant):
        dernier_suivi = enfant.suivis_medicaux.filter(is_active=True).order_by('-date_consultation').first()
        return dernier_suivi.date_consultation if dernier_suivi else ''

    def dehydrate_dernier_suivi_medical_diag(self, enfant):
        dernier_suivi = enfant.suivis_medicaux.filter(is_active=True).order_by('-date_consultation').first()
        return dernier_suivi.diagnostic if dernier_suivi else ''

    def dehydrate_derniere_annee_scolaire(self, enfant):
        dernier_suivi = enfant.suivis_scolaires.filter(is_active=True).order_by('-annee_scolaire').first()
        return dernier_suivi.annee_scolaire if dernier_suivi else ''

    def dehydrate_derniere_classe(self, enfant):
        dernier_suivi = enfant.suivis_scolaires.filter(is_active=True).order_by('-annee_scolaire').first()
        return dernier_suivi.classe if dernier_suivi else ''