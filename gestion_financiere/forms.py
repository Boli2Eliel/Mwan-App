# gestion_financiere/forms.py
from django import forms
from .models import Don, Depense
from enfants_gestion.models import SiteOrphelinat

class DonForm(forms.ModelForm):
    class Meta:
        model = Don
        fields = ['montant', 'donateur', 'date_don', 'description', 'site']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'donateur': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_don': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_superuser:
            self.fields['site'].widget = forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
            self.fields['site'].queryset = SiteOrphelinat.objects.all()
            self.fields['site'].label = "Site de destination du don"
        else:
            del self.fields['site']

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