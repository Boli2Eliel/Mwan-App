from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # --- DÉFINITION DES PERMISSIONS PAR RÔLE ---
    
    # Le GESTIONNAIRE a un contrôle quasi total sur les opérations du quotidien
    gestionnaire_permissions_codenames = [
        'view_enfant', 'add_enfant', 'change_enfant', 'delete_enfant',
        'view_document', 'add_document', 'change_document', 'delete_document',
        'view_suivimedical', 'add_suivimedical', 'change_suivimedical', 'delete_suivimedical',
        'view_suiviscolaire', 'add_suiviscolaire', 'change_suiviscolaire', 'delete_suiviscolaire',
        'view_don', 'add_don', 'change_don',
        'view_depense', 'add_depense', 'change_depense',
    ]
    gestionnaire_permissions = Permission.objects.filter(codename__in=gestionnaire_permissions_codenames)
    gestionnaire_group, created = Group.objects.get_or_create(name='Gestionnaire')
    gestionnaire_group.permissions.set(gestionnaire_permissions)

    # Le COMPTABLE ne voit que la partie financière
    comptable_permissions_codenames = [
        'view_don', 'add_don', 'change_don', 'delete_don',
        'view_depense', 'add_depense', 'change_depense', 'delete_depense',
        'view_comptefinancier', 'view_rapportfinancier' # Permissions hypothétiques pour les rapports
    ]
    comptable_permissions = Permission.objects.filter(codename__in=comptable_permissions_codenames)
    comptable_group, created = Group.objects.get_or_create(name='Comptable')
    comptable_group.permissions.set(comptable_permissions)

    # La SECRÉTAIRE a des droits de consultation et d'ajout limités
    secretaire_permissions_codenames = [
        'view_enfant', 'add_enfant', 'change_enfant', # Peut gérer les dossiers
        'view_document', 'add_document',
        'view_don', 'add_don', # Peut enregistrer un don
    ]
    secretaire_permissions = Permission.objects.filter(codename__in=secretaire_permissions_codenames)
    secretaire_group, created = Group.objects.get_or_create(name='Secrétaire')
    secretaire_group.permissions.set(secretaire_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0001_initial'),
        # Assurez-vous que les migrations des autres apps sont listées ici si nécessaire
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]