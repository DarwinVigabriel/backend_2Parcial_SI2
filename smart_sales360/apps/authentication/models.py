from django.db import models


class Usuarios(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    email_verificado = models.BooleanField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    fecha_ultimo_cambio_password = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'usuarios'


class UserSessions(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING)
    device_info = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    login_at = models.DateTimeField(blank=True, null=True)
    logout_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'user_sessions'


class DispositivosMoviles(models.Model):
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    device_token = models.CharField(max_length=255)
    device_id = models.CharField(unique=True, max_length=255)
    plataforma = models.CharField(max_length=20, blank=True, null=True)
    app_version = models.CharField(max_length=20, blank=True, null=True)
    os_version = models.CharField(max_length=20, blank=True, null=True)
    modelo_dispositivo = models.CharField(max_length=100, blank=True, null=True)
    idioma = models.CharField(max_length=10, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dispositivos_moviles'


class NotificacionPreferencias(models.Model):
    usuario = models.OneToOneField('authentication.Usuarios', models.DO_NOTHING)
    recibir_promociones = models.BooleanField(blank=True, null=True)
    recibir_alertas_stock = models.BooleanField(blank=True, null=True)
    recibir_notificaciones_venta = models.BooleanField(blank=True, null=True)
    recibir_marketing = models.BooleanField(blank=True, null=True)
    recibir_alertas_sistema = models.BooleanField(blank=True, null=True)
    hora_inicio_notificaciones = models.TimeField(blank=True, null=True)
    hora_fin_notificaciones = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notificacion_preferencias'


class Notificaciones(models.Model):
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    dispositivo = models.ForeignKey('authentication.DispositivosMoviles', models.DO_NOTHING, blank=True, null=True)
    leida = models.BooleanField(blank=True, null=True)
    enviada = models.BooleanField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    error_envio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notificaciones'


class AuditLogs(models.Model):
    usuario = models.ForeignKey('authentication.Usuarios', models.DO_NOTHING, blank=True, null=True)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=50, blank=True, null=True)
    registro_id = models.IntegerField(blank=True, null=True)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'audit_logs'
