# gestion_financiere/models.py
from django.db import models
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
    

class Don(models.Model):
    compte = models.ForeignKey(CompteFinancier, on_delete=models.PROTECT)
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT)
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    donateur = models.CharField(max_length=200, blank=True, default="Anonyme")
    date_don = models.DateField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Don de {self.montant}XAF le {self.date_don}"

class Depense(models.Model):
    compte = models.ForeignKey(CompteFinancier, on_delete=models.PROTECT)
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT)
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=100, help_text="Ex: Loyer, Nourriture, Salaires...")
    date_depense = models.DateField()
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dépense de {self.montant}XAF ({self.categorie})"

class Parrainage(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)
    parrain_nom = models.CharField("Nom du parrain/marraine", max_length=200)
    montant_mensuel = models.DecimalField(max_digits=8, decimal_places=2)
    date_debut = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Parrainage de {self.enfant} par {self.parrain_nom}"
    



