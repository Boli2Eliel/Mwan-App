from django.contrib.auth.models import AbstractUser
from django.db import models
from sites_gestion.models import SiteOrphelinat

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('directeur', 'Directeur'),
        ('soignant', 'Soignant'),
        ('comptable', 'Comptable'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # Chaque utilisateur est rattaché à UN site.
    # Si un utilisateur a accès à plusieurs sites, une approche plus complexe
    # (ManyToMany) sera nécessaire, mais commençons simple.
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT, null=True, blank=True)