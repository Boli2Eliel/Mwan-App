from django.contrib.auth.models import AbstractUser
from django.db import models
from sites_gestion.models import SiteOrphelinat

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('Directeur', 'Directeur'),
        ('Comptable', 'Comptable'),
        ('Soignant', 'Soignant'),
        ('Gestionnaire', 'Gestionnaire'),
        ('Bénévole', 'Bénévole'),
        ('Secrétaire', 'Secrétaire'),
        ('RH', 'RH'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # Chaque utilisateur est rattaché à UN site.
    # Si un utilisateur a accès à plusieurs sites, une approche plus complexe
    # (ManyToMany) sera nécessaire, mais commençons simple.
    #site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT, null=True, blank=True)

    sites = models.ManyToManyField(
        SiteOrphelinat,
        blank=True,
        verbose_name="Sites autorisés",
        help_text="Les sites auxquels cet utilisateur a accès. Laisser vide pour donner accès à tous les sites (pour les rôles globaux)."
    )

    is_comptable_central = models.BooleanField(
        "Comptable Central",
        default=False,
        help_text="Cochez cette case si l'utilisateur doit avoir accès aux finances de tous les sites."
    )