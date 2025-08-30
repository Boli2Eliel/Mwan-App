# enfants_gestion/forms.py
from django import forms
from .models import Enfant, SuiviMedical, SuiviScolaire, Document
from django.forms import inlineformset_factory
from sites_gestion.models import SiteOrphelinat


class EnfantForm(forms.ModelForm):
    class Meta:
        model = Enfant
        fields = [
            'nom', 'prenom', 'date_naissance', 'sexe', 'lieu_naissance', 
            'date_arrivee', 'statut', 'date_depart', 'site',
            'motif_admission', 'histoire', 'photo'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'prenom': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'date_arrivee': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'date_depart': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'sexe': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'statut': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'motif_admission': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'histoire': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'file-input file-input-bordered file-input-sm w-full'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_superuser:
            self.fields['site'].widget = forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
            self.fields['site'].queryset = SiteOrphelinat.objects.all()
            self.fields['site'].required = True
        else:
            del self.fields['site']

    def clean(self):
        cleaned_data = super().clean()
        statut = cleaned_data.get("statut")
        date_depart = cleaned_data.get("date_depart")
        statuts_de_depart = ['adopte', 'reunifie', 'majeur']
        if statut in statuts_de_depart and not date_depart:
            self.add_error('date_depart', "La date de départ est obligatoire pour ce statut.")
        if statut not in statuts_de_depart:
            cleaned_data['date_depart'] = None
        return cleaned_data
    
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['type_document', 'description', 'fichier']
        widgets = {
            'type_document': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'description': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full', 'placeholder': 'Description du document'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'file-input file-input-bordered file-input-sm w-full'}),
        }

    # CORRECTION : Remplacer __init__ par clean() est plus robuste pour la suppression.
    def clean(self):
        cleaned_data = super().clean()
        # Si la case DELETE est cochée, on considère le formulaire comme valide
        # même si d'autres champs (comme 'fichier') sont vides.
        if self.cleaned_data.get('DELETE', False):
            return {} # On stoppe la validation pour cette ligne.
        return cleaned_data

DocumentFormSet = inlineformset_factory(
    Enfant,
    Document,
    form=DocumentForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True
)

class SuiviMedicalForm(forms.ModelForm):
    class Meta:
        model = SuiviMedical
        fields = ['date_consultation', 'type_consultation', 'medecin', 'diagnostic', 'traitement', 'notes']
        widgets = {
            'date_consultation': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'type_consultation': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'medecin': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'diagnostic': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'traitement': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'placeholder' not in field.widget.attrs:
                # Pour les champs de date, un placeholder n'est pas utile
                if not isinstance(field.widget, forms.DateInput):
                    field.widget.attrs['placeholder'] = field.label


class SuiviScolaireForm(forms.ModelForm):
    class Meta:
        model = SuiviScolaire
        fields = ['annee_scolaire', 'ecole', 'classe', 'resultats']
        widgets = {
            # On ajoute les classes pour un style cohérent et une taille réduite
            'annee_scolaire': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'ecole': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'classe': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'resultats': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-32'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On ajoute dynamiquement les placeholders à partir des labels
        for field_name, field in self.fields.items():
            if 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = field.label


# ============== IMPORT/ EXPORT ===================
class ExportFilterForm(forms.Form):
    STATUT_CHOICES = [
        ('', 'Tous les statuts'),
        ('actifs', 'Dossiers Actifs'),
        ('inactifs', 'Dossiers Archivés'),
    ]
    """FORMAT_CHOICES = [
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV'),
    ]"""

    statut = forms.ChoiceField(choices=STATUT_CHOICES, required=False, label="Filtrer par statut",
                               widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}))
    date_debut = forms.DateField(required=False, label="Arrivée après le",
                                 widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}))
    date_fin = forms.DateField(required=False, label="Arrivée avant le",
                               widget=forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}))
    
    # Le champ 'site' sera ajouté dynamiquement pour les superusers dans la vue
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_superuser:
            sites = [('', 'Tous les sites')] + list(SiteOrphelinat.objects.values_list('pk', 'nom'))
            self.fields['site'] = forms.ChoiceField(
                choices=sites, 
                required=False, 
                label="Filtrer par site",
                widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
            )