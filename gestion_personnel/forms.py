from django import forms
from django.db import transaction
from .models import Employe
from utilisateurs.models import CustomUser
from sites_gestion.models import SiteOrphelinat

class EmployeCreateForm(forms.Form):
    # --- Champs pour l'Employé ---
    nom = forms.CharField(label="Nom de l'employé", max_length=100,
        widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    prenom = forms.CharField(label="Prénom de l'employé", max_length=100,
        widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    poste = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    type_contrat = forms.ChoiceField(choices=Employe.TYPE_CONTRAT_CHOICES,
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
        
    date_embauche = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}))
        
    telephone = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    adresse = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}), required=False)
    
    # --- Checkbox pour créer un compte ---
    creer_compte_utilisateur = forms.BooleanField(
        label="Créer un compte d'accès pour cet employé", 
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox',
            'x-model': 'creerCompte'  # <-- La correction est ici
        })
    )
    
    # --- Champs pour le Compte Utilisateur (conditionnels) ---
    site = forms.ModelChoiceField(queryset=SiteOrphelinat.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
        
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    email = forms.EmailField(required=False,
        widget=forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}))
        
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
        
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(
        attrs={'class': 'input input-bordered input-sm w-full'}), required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not self.user.is_superuser:
            del self.fields['site']

    @transaction.atomic
    def save(self):
        # Création de l'employé
        employe = Employe.objects.create(
            nom=self.cleaned_data['nom'],
            prenom=self.cleaned_data['prenom'],
            poste=self.cleaned_data['poste'],
            type_contrat=self.cleaned_data['type_contrat'],
            date_embauche=self.cleaned_data['date_embauche'],
            telephone=self.cleaned_data['telephone'],
            adresse=self.cleaned_data['adresse'],
        )

        # Si la case est cochée, on crée aussi le compte utilisateur
        if self.cleaned_data.get('creer_compte_utilisateur'):
            site = self.cleaned_data.get('site') if self.user.is_superuser else self.user.site
            if not site:
                raise forms.ValidationError("Un site doit être sélectionné pour créer un utilisateur.")

            user = CustomUser.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['prenom'],
                last_name=self.cleaned_data['nom'],
                site=site,
                role=self.cleaned_data['role']
            )
            employe.utilisateur = user
            employe.save()
            
        return employe


class EmployeUpdateForm(forms.Form):
    # --- Champs pour l'Employé (identiques à la création) ---
    nom = forms.CharField(label="Nom de l'employé", max_length=100, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    prenom = forms.CharField(label="Prénom de l'employé", max_length=100, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    poste = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    type_contrat = forms.ChoiceField(choices=Employe.TYPE_CONTRAT_CHOICES, widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
    date_embauche = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}))
    telephone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    adresse = forms.CharField(widget=forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}), required=False)
    
    # --- Checkbox et champs pour le compte (identiques à la création) ---
    creer_compte_utilisateur = forms.BooleanField(label="Créer un compte d'accès pour cet employé", required=False, widget=forms.CheckboxInput(attrs={'class': 'checkbox', 'x-model': 'creerCompte'}))
    site = forms.ModelChoiceField(queryset=SiteOrphelinat.objects.all(), required=False, widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'input input-bordered input-sm w-full'}), required=False)

    def __init__(self, *args, **kwargs):
        # On récupère l'instance de l'employé et l'utilisateur connecté
        self.instance = kwargs.pop('instance', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # On pré-remplit le formulaire avec les données de l'employé existant
        if self.instance:
            self.fields['nom'].initial = self.instance.nom
            self.fields['prenom'].initial = self.instance.prenom
            # ... continuez pour tous les autres champs de l'employé
            self.fields['poste'].initial = self.instance.poste
            self.fields['type_contrat'].initial = self.instance.type_contrat
            self.fields['date_embauche'].initial = self.instance.date_embauche
            self.fields['telephone'].initial = self.instance.telephone
            self.fields['adresse'].initial = self.instance.adresse

        # Logique pour le champ 'site' (pour le superuser)
        if not self.user.is_superuser:
            del self.fields['site']

    @transaction.atomic
    def save(self):
        # 1. Mettre à jour la fiche de l'employé
        employe = self.instance
        employe.nom = self.cleaned_data['nom']
        employe.prenom = self.cleaned_data['prenom']
        employe.poste = self.cleaned_data['poste']
        employe.type_contrat = self.cleaned_data['type_contrat']
        employe.date_embauche = self.cleaned_data['date_embauche']
        employe.telephone = self.cleaned_data['telephone']
        employe.adresse = self.cleaned_data['adresse']
        employe.save()

        # 2. Si la case est cochée ET que l'employé n'a pas déjà de compte...
        if self.cleaned_data.get('creer_compte_utilisateur') and not employe.utilisateur:
            # ...on crée le compte utilisateur comme dans le formulaire de création
            site = self.cleaned_data.get('site') if self.user.is_superuser else self.user.site
            if not site:
                raise forms.ValidationError("Un site doit être sélectionné pour créer un utilisateur.")
            
            user = CustomUser.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['prenom'],
                last_name=self.cleaned_data['nom'],
                site=site,
                role=self.cleaned_data['role']
            )
            employe.utilisateur = user
            employe.save()
            
        return employe