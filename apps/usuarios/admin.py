from django.contrib import admin
from .models import Persona, Perfil, AuditLog

admin.site.register(Persona)
admin.site.register(Perfil)
admin.site.register(AuditLog)
