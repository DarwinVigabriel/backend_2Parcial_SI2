from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Usuarios, UserSessions, DispositivosMoviles, NotificacionPreferencias, Notificaciones, AuditLogs


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'apellido', 'activo')
    search_fields = ('email', 'nombre', 'apellido')
    
    def save_model(self, request, obj, form, change):
        # Si es creación nueva o la contraseña cambió, hashearla
        if change and 'password_hash' in form.changed_data:
            # Edición y cambió la contraseña
            obj.password_hash = make_password(obj.password_hash)
        elif not change:
            # Creación nueva
            if obj.password_hash:
                obj.password_hash = make_password(obj.password_hash)
        super().save_model(request, obj, form, change)


@admin.register(UserSessions)
class UserSessionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'login_at', 'logout_at', 'is_active')


@admin.register(DispositivosMoviles)
class DispositivosMovilesAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'usuario', 'plataforma')


@admin.register(NotificacionPreferencias)
class NotificacionPreferenciasAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'recibir_promociones')


@admin.register(Notificaciones)
class NotificacionesAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'enviada', 'leida')


@admin.register(AuditLogs)
class AuditLogsAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'tabla_afectada', 'created_at')
