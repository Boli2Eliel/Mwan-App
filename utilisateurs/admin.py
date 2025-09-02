# utilisateurs/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Configuration de l'interface d'administration pour le modèle CustomUser.
    Hérite de UserAdmin pour conserver la gestion sécurisée des mots de passe.
    """
    
    # Champs affichés sur la page de modification d'un utilisateur
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Supplémentaires', {'fields': ('role', 'sites', 'is_comptable_central')}), # <-- MODIFIÉ
    )
    
    # Champs affichés sur la page de création d'un nouvel utilisateur
    # C'est cette section qui garantit l'affichage du double champ de mot de passe
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'sites', 'is_comptable_central')}), # <-- MODIFIÉ
    )
    
    # Champs affichés dans la liste des utilisateurs
    list_display = ('username', 'email', 'is_staff', 'is_comptable_central') # 'site' n'est plus un champ unique
    list_filter = ('is_staff', 'is_superuser', 'groups', 'sites') # <-- MODIFIÉ