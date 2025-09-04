from django import forms
from .models import Transaction, CompteFinancier, Parrainage, Enfant
from utilisateurs.models import CustomUser
from sites_gestion.models import SiteOrphelinat

class TransactionForm(forms.ModelForm):
    CATEGORIE_ENTREE_CHOICES = [('', '---------')] + Transaction.CATEGORIE_ENTREE_CHOICES
    CATEGORIE_SORTIE_CHOICES = [('', '---------')] + Transaction.CATEGORIE_SORTIE_CHOICES

    categorie = forms.ChoiceField(
        choices=[('', '---------')],
        required=True,
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full'})
    )

    class Meta:
        model = Transaction
        fields = ['compte', 'type_transaction', 'categorie', 'montant', 'date_transaction', 'description', 'parrainage_lie']
        widgets = {
            'compte': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'type_transaction': forms.HiddenInput(), # Le champ est maintenant caché
            'montant': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_transaction': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full h-24'}),
            'parrainage_lie': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)

        sites_autorises = SiteOrphelinat.objects.all()
        if user and not user.is_superuser:
            sites_autorises = user.sites.all()
        
        self.fields['compte'].queryset = CompteFinancier.objects.filter(site__in=sites_autorises)
        self.fields['parrainage_lie'].queryset = Parrainage.objects.filter(enfant__site__in=sites_autorises)

        if transaction_type == 'entree':
            self.fields['categorie'].choices = self.CATEGORIE_ENTREE_CHOICES
        elif transaction_type == 'sortie':
            self.fields['categorie'].choices = self.CATEGORIE_SORTIE_CHOICES

            
class ParrainageForm(forms.ModelForm):
    class Meta:
        model = Parrainage
        fields = ['enfant', 'parrain_nom', 'montant_mensuel', 'date_debut', 'date_fin']
        widgets = {
            'enfant': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'parrain_nom': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'montant_mensuel': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered input-sm w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On ne propose que les enfants qui n'ont pas de parrainage actif
        enfants_parraines_ids = Parrainage.objects.filter(is_active=True).values_list('enfant_id', flat=True)
        
        # Si on modifie un parrainage existant, on n'exclut pas l'enfant actuel de la liste
        if self.instance and self.instance.pk:
            enfants_parraines_ids = [pk for pk in enfants_parraines_ids if pk != self.instance.enfant.pk]

        self.fields['enfant'].queryset = Enfant.objects.filter(is_active=True).exclude(id__in=enfants_parraines_ids)

class FinanceExportForm(forms.Form):
    TYPE_CHOICES = [
        ('transactions', 'Toutes les Transactions'),
        ('parrainages', 'Liste des Parrainages')
    ]
    FORMAT_CHOICES = [
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV')
    ]

    type_donnees = forms.ChoiceField(choices=TYPE_CHOICES, label="Type de données à exporter")
    date_debut = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Date de début")
    date_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Date de fin")
    format_fichier = forms.ChoiceField(choices=FORMAT_CHOICES, label="Format du fichier")