from django.contrib import admin

from utilisateurs.models import CustomUser


admin.site.register(CustomUser)
