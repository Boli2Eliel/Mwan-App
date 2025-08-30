from django.db import models
from django.conf import settings
from sites_gestion.models import SiteOrphelinat
from simple_history.models import HistoricalRecords

# Modèle principal pour l'enfant
class Enfant(models.Model):
    # --- Champs existants ---
    site = models.ForeignKey(SiteOrphelinat, on_delete=models.PROTECT, verbose_name="Site d'accueil")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField("Date de naissance")
    
    # --- Champs enrichis ---
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    STATUT_CHOICES = [
        ('accueilli', 'Accueilli'),
        ('adopte', 'Adopté'),
        ('reunifie', 'Réunifié (famille)'),
        ('majeur', 'Majeur / Départ'),
    ]

    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    lieu_naissance = models.CharField("Lieu de naissance", max_length=150, blank=True)
    photo = models.ImageField(upload_to='photos_enfants/', blank=True, null=True)
    date_arrivee = models.DateField("Date d'arrivée")
    motif_admission = models.TextField("Motif d'admission", blank=True)
    histoire = models.TextField("Histoire de l'enfant", blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='accueilli')
    date_depart = models.DateField("Date de départ", null=True, blank=True)
    is_active = models.BooleanField(default=True)


    history = HistoricalRecords()
    
    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"

    def __str__(self):
        return f"{self.prenom} {self.nom}"

# Modèle pour les documents importants de l'enfant
class Document(models.Model):
    TYPE_DOCUMENT_CHOICES = [
        ('acte_naissance', 'Acte de naissance'),
        ('jugement', "Jugement d'admission"),
        ('carnet_sante', 'Carnet de santé'),
        ('bulletin_scolaire', 'Bulletin scolaire'),
        ('autre', 'Autre'),
    ]
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=20, choices=TYPE_DOCUMENT_CHOICES)
    description = models.CharField(max_length=255,  null=True, blank=True)
    fichier = models.FileField(upload_to='documents_enfants/')
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_document_display()} pour {self.enfant}"

# Modèle pour le suivi médical détaillé
class SuiviMedical(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='suivis_medicaux')
    date_consultation = models.DateField()
    type_consultation = models.CharField(max_length=100, help_text="Ex: Généraliste, Vaccin, Dentiste...")
    medecin = models.CharField(max_length=100, blank=True)
    diagnostic = models.TextField()
    traitement = models.TextField(blank=True)
    notes = models.TextField("Notes supplémentaires", blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_consultation']
        verbose_name = "Suivi Médical"

    def __str__(self):
        return f"Consultation du {self.date_consultation} pour {self.enfant}"

# Modèle pour le suivi de la scolarité
class SuiviScolaire(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='suivis_scolaires')
    annee_scolaire = models.CharField(max_length=9, help_text="Format: 2024-2025")
    ecole = models.CharField("Établissement scolaire", max_length=150)
    classe = models.CharField(max_length=50)
    resultats = models.TextField("Résultats et appréciations", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-annee_scolaire']
        unique_together = ('enfant', 'annee_scolaire') # Un seul suivi par an par enfant
        verbose_name = "Suivi Scolaire"

    def __str__(self):
        return f"Scolarité {self.annee_scolaire} pour {self.enfant}"

# Modèle pour les notes d'évolution (comportement, développement personnel)
class NoteEvolutive(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='notes_evolutives')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    note = models.TextField("Note sur le comportement/développement")
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Note Évolutive"
    
    def __str__(self):
        return f"Note du {self.date_creation.strftime('%d/%m/%Y')} pour {self.enfant}"