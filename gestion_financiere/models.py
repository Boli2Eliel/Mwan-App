from django.db import models
from django.conf import settings
from enfants_gestion.models import Enfant
from sites_gestion.models import SiteOrphelinat
from django.db.models import Sum
from datetime import date
from dateutil.relativedelta import relativedelta
from enfants_gestion.models import Enfant


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
    date_fin = models.DateField(null=True, blank=True, help_text="Laissez vide si le parrainage est toujours actif.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Parrainage de {self.enfant} par {self.parrain_nom}"

    def get_statut_paiement(self):
        """
        Calcule l'état des paiements pour ce parrainage en se basant sur les transactions.
        """
        if not self.is_active or self.date_fin and self.date_fin < date.today():
            return {'statut': 'Terminé', 'couleur': 'ghost', 'difference': 0}

        today = date.today()
        
        # Calculer le nombre de mois écoulés depuis le début
        delta = relativedelta(today, self.date_debut)
        mois_ecoules = delta.years * 12 + delta.months + 1
        montant_attendu = mois_ecoules * self.montant_mensuel

        # CORRECTION : On somme les transactions liées à ce parrainage
        total_verse = self.transactions.filter(is_active=True, type_transaction='entree').aggregate(total=Sum('montant'))['total'] or 0

        difference = total_verse - montant_attendu

        if difference >= 0:
            return {'statut': 'À jour', 'couleur': 'success', 'difference': difference}
        elif abs(difference) > self.montant_mensuel:
            return {'statut': 'En retard', 'couleur': 'error', 'difference': difference}
        else:
            return {'statut': 'Partiel', 'couleur': 'warning', 'difference': difference}

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