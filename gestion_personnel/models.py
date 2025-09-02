# gestion_personnel/models.py
from django.db import models
from django.conf import settings
from sites_gestion.models import SiteOrphelinat

class Employe(models.Model):
    # Le lien vers le compte utilisateur est maintenant OPTIONNEL.
    # on_delete=models.SET_NULL garantit que si on supprime le compte utilisateur,
    # la fiche de l'employé est conservée (son compte passe à NULL).
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Informations de base, maintenant directement sur l'employé
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    
    # Informations enrichies
    poste = models.CharField(max_length=100)
    TYPE_CONTRAT_CHOICES = [
        ('CDI', 'Contrat à Durée Indéterminée'),
        ('CDD', 'Contrat à Durée Déterminée'),
        ('Benevole', 'Bénévole'),
    ]
    type_contrat = models.CharField(max_length=10, choices=TYPE_CONTRAT_CHOICES, default='CDI')
    date_embauche = models.DateField()
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    salaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField("Notes confidentielles", blank=True)
    
    # Champ pour le soft delete
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def site(self):
        # Un employé peut être lié à plusieurs sites via son compte utilisateur.
        # Cette propriété renvoie le premier site de la liste pour un affichage simple.
        if self.utilisateur and self.utilisateur.sites.exists():
            return self.utilisateur.sites.first()
        return None