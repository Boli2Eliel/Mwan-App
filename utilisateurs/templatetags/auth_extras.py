from django import template
from django.contrib.auth.models import Group 

register = template.Library()

@register.simple_tag
def has_group(user, group_name):
    """Vérifie si un utilisateur appartient à un groupe."""
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except Group.DoesNotExist:
        return False