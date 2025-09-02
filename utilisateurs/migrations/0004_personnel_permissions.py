from django.db import migrations
from django.contrib.auth.models import ContentType

def add_personnel_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # On récupère les permissions en filtrant par le nom de l'application
    # et les noms de code des permissions. C'est la méthode la plus fiable.
    permissions_codenames = [
        'view_employe', 'add_employe', 'change_employe', 'delete_employe',
    ]
    personnel_permissions = Permission.objects.filter(
        content_type__app_label='gestion_personnel',
        codename__in=permissions_codenames
    )

    # Création du groupe RH (s'il n'existe pas)
    rh_group, created = Group.objects.get_or_create(name='RH')
    rh_group.permissions.add(*personnel_permissions)

    # Ajout des permissions au groupe Gestionnaire (s'il n'existe pas)
    gestionnaire_group, created = Group.objects.get_or_create(name='Gestionnaire')
    gestionnaire_group.permissions.add(*personnel_permissions)

    # La Secrétaire ne peut que voir la liste du personnel
    secretaire_group, created = Group.objects.get_or_create(name='Secrétaire')
    try:
        view_perm = Permission.objects.get(
            content_type__app_label='gestion_personnel',
            codename='view_employe'
        )
        secretaire_group.permissions.add(view_perm)
    except Permission.DoesNotExist:
        # Gère le cas où la permission n'existerait pas encore, bien que peu probable ici.
        print("Avertissement : la permission 'view_employe' n'a pas été trouvée.")


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0003_customuser_is_comptable_central_and_more'),
        ('utilisateurs', '0002_initial_groups'), # Dépend de la migration précédente
        ('gestion_personnel', '0001_initial'), # Dépend de la création du modèle Employe
    ]

    operations = [
        migrations.RunPython(add_personnel_permissions),
    ]

    