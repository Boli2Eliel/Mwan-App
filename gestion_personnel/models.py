# gestion_personnel/models.py
from django.db import models
from django.conf import settings
from sites_gestion.models import SiteOrphelinat
from utilisateurs.models import CustomUser

class Employe(models.Model):
    utilisateur = models.OneToOneField(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    sites = models.ManyToManyField(
        SiteOrphelinat,
        blank=True,
        verbose_name="Sites d'affectation"
    )

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
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
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"