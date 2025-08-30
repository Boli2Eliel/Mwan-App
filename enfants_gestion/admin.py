# enfants_gestion/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin # <-- IMPORTEZ
from .models import Enfant
from .resources import EnfantResource # <-- IMPORTEZ
from .models import Document, SuiviMedical

admin.site.site_header = "Administration KidsApp"

@admin.register(Enfant)
class EnfantAdmin(ImportExportModelAdmin): # <-- UTILISEZ CETTE CLASSE
    resource_classes = [EnfantResource] # <-- ASSOCIEZ LA RESSOURCE
    list_display = ('nom', 'prenom', 'site', 'statut', 'is_active')
    list_filter = ('site', 'statut', 'is_active')


admin.site.register(Document)
admin.site.register(SuiviMedical)