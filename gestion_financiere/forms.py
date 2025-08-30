# gestion_financiere/forms.py
from django import forms
from .models import Don, Depense, CompteFinancier
from enfants_gestion.models import SiteOrphelinat

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
    class Meta:
        model = Depense
        fields = ['montant', 'categorie', 'date_depense', 'description', 'site']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'categorie': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_depense': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_superuser:
            self.fields['site'].widget = forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
            self.fields['site'].queryset = SiteOrphelinat.objects.all()
        else:
            del self.fields['site']