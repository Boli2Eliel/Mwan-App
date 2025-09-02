from django.db import migrations

def align_roles_with_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # --- 1. SUPPRESSION DES ANCIENS GROUPES (pour repartir de zéro) ---
    Group.objects.all().delete()

    # --- 2. DÉFINITION DES PERMISSIONS POUR CHAQUE RÔLE ---
    
    # RÔLE : Directeur (aura toutes les permissions)
    directeur_group, created = Group.objects.get_or_create(name='Directeur')
    all_permissions = Permission.objects.all()
    directeur_group.permissions.set(all_permissions)

    # RÔLE : Comptable (droits financiers)
    comptable_permissions = Permission.objects.filter(
        content_type__app_label__in=['gestion_financiere'],
    )
    comptable_group, created = Group.objects.get_or_create(name='Comptable')
    comptable_group.permissions.set(comptable_permissions)
    
    # RÔLE : Soignant (droits sur les enfants et suivis)
    soignant_permissions_codenames = [
        'view_enfant', 'change_enfant',
        'view_suivimedical', 'add_suivimedical', 'change_suivimedical',
        'view_suiviscolaire', 'add_suiviscolaire', 'change_suiviscolaire',
    ]
    soignant_permissions = Permission.objects.filter(codename__in=soignant_permissions_codenames)
    soignant_group, created = Group.objects.get_or_create(name='Soignant')
    soignant_group.permissions.set(soignant_permissions)
    
    # RÔLE : Gestionnaire (contrôle total sur les opérations du quotidien)
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

    # RÔLE : Bénévole (droits de consultation uniquement)
    benevole_permissions_codenames = [
        'view_enfant', 'view_don', 'view_depense',
    ]
    benevole_permissions = Permission.objects.filter(codename__in=benevole_permissions_codenames)
    benevole_group, created = Group.objects.get_or_create(name='Bénévole')
    benevole_group.permissions.set(benevole_permissions)

    # RÔLE : Secrétaire (droits de consultation et d'ajout limités)
    secretaire_permissions_codenames = [
        'view_enfant', 'add_enfant', 'change_enfant',
        'view_document', 'add_document',
        'view_don', 'add_don',
    ]
    secretaire_permissions = Permission.objects.filter(codename__in=secretaire_permissions_codenames)
    secretaire_group, created = Group.objects.get_or_create(name='Secrétaire')
    secretaire_group.permissions.set(secretaire_permissions)

    # RÔLE : RH (droits sur le personnel)
    rh_permissions = Permission.objects.filter(
        content_type__app_label__in=['gestion_personnel'],
    )
    rh_group, created = Group.objects.get_or_create(name='RH')
    rh_group.permissions.set(rh_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0004_personnel_permissions'), # Assurez-vous que c'est le nom de votre dernière migration
    ]

    operations = [
        migrations.RunPython(align_roles_with_groups),
    ]