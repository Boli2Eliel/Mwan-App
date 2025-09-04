from import_export import resources, fields
from .models import Transaction

class TransactionResource(resources.ModelResource):
    # On ajoute des champs personnalisés pour récupérer les noms plutôt que les IDs
    compte = fields.Field(attribute='compte__nom', column_name='Compte Financier')
    parrain = fields.Field(attribute='parrainage_lie__parrain_nom', column_name='Parrain (si applicable)')
    enfant_parraine = fields.Field(attribute='parrainage_lie__enfant__prenom', column_name='Enfant (si parrainage)')
    cree_par = fields.Field(attribute='cree_par__username', column_name='Créé par')

    class Meta:
        model = Transaction
        # On définit les champs à inclure dans l'export
        fields = (
            'id',
            'date_transaction',
            'type_transaction',
            'categorie',
            'montant',
            'description',
            'compte',
            'parrain',
            'enfant_parraine',
            'cree_par',
        )
        # On définit l'ordre des colonnes dans le fichier exporté
        export_order = fields

    def dehydrate_montant(self, transaction):
        """
        Méthode pour formater le montant : positif pour les entrées, négatif pour les sorties.
        """
        if transaction.type_transaction == 'sortie':
            return -transaction.montant
        return transaction.montant