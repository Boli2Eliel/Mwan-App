from django.db import models
from django.conf import settings
from enfants_gestion.models import Enfant
from sites_gestion.models import SiteOrphelinat

class CompteFinancier(models.Model):
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT)
    nom = models.CharField(max_length=100)
    solde_initial = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.site.nom})"

class Parrainage(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='parrainages')
    parrain_nom = models.CharField("Nom du parrain/marraine", max_length=200)
    montant_mensuel = models.DecimalField(max_digits=8, decimal_places=2)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Parrainage de {self.enfant} par {self.parrain_nom}"

# NOUVEAU MODÈLE CENTRAL
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    CATEGORIE_ENTREE_CHOICES = [
        ('Don', 'Don'),
        ('Parrainage', 'Versement de Parrainage'),
        ('Subvention', 'Subvention'),
        ('Autre', 'Autre Entrée'),
    ]
    CATEGORIE_SORTIE_CHOICES = [
        ('Nourriture', 'Nourriture'),
        ('Loyer', 'Loyer'),
        ('Salaires', 'Salaires'),
        ('Santé', 'Santé'),
        ('Scolarité', 'Scolarité'),
        ('Entretien', 'Entretien & Fournitures'),
        ('Autre', 'Autre Dépense'),
    ]

    compte = models.ForeignKey(CompteFinancier, on_delete=models.PROTECT, related_name='transactions')
    type_transaction = models.CharField(max_length=10, choices=TYPE_CHOICES)
    categorie = models.CharField(max_length=50) # Les choix seront gérés dans le formulaire
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_transaction = models.DateField()
    description = models.TextField()
    
    # Liens optionnels pour plus de détails
    parrainage_lie = models.ForeignKey(Parrainage, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    is_active = models.BooleanField(default=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date_transaction']

    def __str__(self):
        prefix = "+" if self.type_transaction == 'entree' else "-"
        return f"{self.date_transaction}: {prefix}{self.montant} XAF ({self.categorie})"

# Les anciens modèles Don, Depense, VersementParrainage peuvent maintenant être supprimés ou commentés.