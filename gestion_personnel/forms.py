from django import forms
from django.db import transaction
from .models import Employe
from utilisateurs.models import CustomUser
from sites_gestion.models import SiteOrphelinat

class EmployeForm(forms.ModelForm):
    # --- Champs pour la gestion du compte utilisateur (maintenant sans le champ 'user_action') ---
    username = forms.CharField(label="Nom d'utilisateur", required=False, widget=forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'input input-bordered input-sm w-full'}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'input input-bordered input-sm w-full'}), required=False)
    lier_utilisateur = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(employe__isnull=True),
        required=False,
        label="Choisir un compte existant non-assigné",
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
    )

    class Meta:
        model = Employe
        fields = ['nom', 'prenom', 'poste', 'type_contrat', 'date_embauche', 'telephone', 'adresse', 'sites']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'prenom': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'poste': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'type_contrat': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'telephone': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'adresse': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'sites': forms.CheckboxSelectMultiple, # Widget simple de cases à cocher
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.request_user and not self.request_user.is_superuser:
            self.fields['sites'].queryset = self.request_user.sites.all()
        else:
            self.fields['sites'].queryset = SiteOrphelinat.objects.all()

        if self.instance and self.instance.pk and self.instance.utilisateur:
            del self.fields['username']
            del self.fields['email']
            del self.fields['role']
            del self.fields['password']
            del self.fields['lier_utilisateur']

    @transaction.atomic
    def save(self, commit=True, action='none'):
        employe = super().save(commit=True)
        
        if not employe.utilisateur:
            if action == 'create':
                if not self.cleaned_data.get('username') or not self.cleaned_data.get('password'):
                    raise forms.ValidationError("Le nom d'utilisateur et le mot de passe sont requis pour créer un compte.")
                
                sites_selectionnes = self.cleaned_data.get('sites')
                user = CustomUser.objects.create_user(
                    username=self.cleaned_data['username'],
                    email=self.cleaned_data.get('email', ''),
                    password=self.cleaned_data['password'],
                    first_name=self.cleaned_data['prenom'],
                    last_name=self.cleaned_data['nom'],
                    role=self.cleaned_data.get('role')
                )
                if sites_selectionnes:
                    user.sites.set(sites_selectionnes)
                employe.utilisateur = user
                employe.save()
            
            elif action == 'link':
                utilisateur_a_lier = self.cleaned_data.get('lier_utilisateur')
                if utilisateur_a_lier:
                    employe.utilisateur = utilisateur_a_lier
                    employe.save()
                    
        return employe