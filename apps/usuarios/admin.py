from django.contrib import admin
from .models import Usuario, Persona, TipoUsuario, HistorialTipoUsuario


admin.site.register( Usuario )

admin.site.register( Persona )

admin.site.register( TipoUsuario )

admin.site.register( HistorialTipoUsuario )