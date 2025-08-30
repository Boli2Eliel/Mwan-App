# gestion_financiere/forms.py
from django import forms
from .models import Don, Depense, CompteFinancier
from enfants_gestion.models import SiteOrphelinat
from django.db.models import Sum, Q

class DonForm(forms.ModelForm):
    class Meta:
        model = Don
        fields = ['site', 'compte', 'montant', 'donateur', 'date_don', 'description' ]
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'donateur': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_don': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Logique pour les utilisateurs normaux (ne change pas)
        if user and not user.is_superuser:
            del self.fields['site']
            if user.site:
                self.fields['compte'].queryset = CompteFinancier.objects.filter(is_active=True, site=user.site)
        
        # Logique améliorée pour le super-administrateur
        elif user and user.is_superuser:
            self.fields['site'].widget = forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'onchange': 'updateComptes(this.value)'
            })
            self.fields['site'].queryset = SiteOrphelinat.objects.all()
            self.fields['site'].required = True
            
            self.fields['compte'].queryset = CompteFinancier.objects.none() # Commence vide par défaut

            # Si le formulaire est soumis (lié à des données)...
            if self.is_bound:
                try:
                    site_id = int(self.data.get('site'))
                    self.fields['compte'].queryset = CompteFinancier.objects.filter(site__id=site_id)
                except (ValueError, TypeError):
                    pass  # Gère le cas où 'site' n'est pas un nombre valide
            # Si on modifie un objet existant, on pré-remplit les comptes
            elif self.instance.pk and self.instance.site:
                self.fields['compte'].queryset = CompteFinancier.objects.filter(site=self.instance.site)


class DepenseForm(forms.ModelForm):
    autoriser_solde_negatif = forms.BooleanField(
        required=False, 
        label="Forcer la transaction même si le solde devient négatif",
        widget=forms.CheckboxInput(attrs={'class': 'checkbox checkbox-sm'})
    )

    class Meta:
        model = Depense
        fields = ['site','compte', 'montant', 'categorie', 'date_depense', 'description', 'autoriser_solde_negatif']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'categorie': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_depense': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Logique pour les utilisateurs normaux
        if user and not user.is_superuser:
            del self.fields['site']
            if user.site:
                self.fields['compte'].queryset = CompteFinancier.objects.filter(is_active=True, site=user.site)
        
        # Logique améliorée pour le super-administrateur
        elif user and user.is_superuser:
            self.fields['site'].widget = forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'onchange': 'updateComptes(this.value)'
            })
            self.fields['site'].queryset = SiteOrphelinat.objects.all()
            self.fields['site'].required = True
            
            self.fields['compte'].queryset = CompteFinancier.objects.none()

            # CORRECTION : On recharge la liste des comptes si le formulaire est soumis
            if self.is_bound:
                try:
                    site_id = int(self.data.get('site'))
                    self.fields['compte'].queryset = CompteFinancier.objects.filter(site__id=site_id)
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk and self.instance.site:
                self.fields['compte'].queryset = CompteFinancier.objects.filter(site=self.instance.site)

    def clean(self):
        cleaned_data = super().clean()
        compte = cleaned_data.get('compte')
        montant_depense = cleaned_data.get('montant')
        autoriser_solde_negatif = cleaned_data.get('autoriser_solde_negatif')

        if compte and montant_depense:
            # Calcul du solde actuel
            total_dons = Don.objects.filter(compte=compte, is_active=True).aggregate(Sum('montant'))['montant__sum'] or 0
            # On exclut la dépense actuelle si on est en train de la modifier
            depenses_existantes = Depense.objects.filter(compte=compte, is_active=True).exclude(pk=self.instance.pk)
            total_depenses = depenses_existantes.aggregate(Sum('montant'))['montant__sum'] or 0
            solde_actuel = (compte.solde_initial + total_dons) - total_depenses

            if solde_actuel < montant_depense and not autoriser_solde_negatif:
                raise forms.ValidationError(
                    f"Le solde du compte ({solde_actuel} XAF) est insuffisant pour cette dépense. "
                    f"Cochez la case pour forcer la transaction."
                )
        return cleaned_data