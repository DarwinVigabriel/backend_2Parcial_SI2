from django.contrib import admin
from .models import Usuarios, UserSessions, DispositivosMoviles, NotificacionPreferencias, Notificaciones, AuditLogs


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'apellido', 'activo')
    search_fields = ('email', 'nombre', 'apellido')


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
