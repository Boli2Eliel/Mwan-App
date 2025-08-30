from django.db import models

class SiteOrphelinat(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    adresse = models.TextField(blank=True)
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.ville}, {self.pays})"