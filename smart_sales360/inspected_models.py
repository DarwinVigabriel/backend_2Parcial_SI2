# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuditLogs(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=50, blank=True, null=True)
    registro_id = models.IntegerField(blank=True, null=True)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'audit_logs'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CarritoItems(models.Model):
    carrito = models.ForeignKey('Carritos', models.DO_NOTHING)
    producto = models.ForeignKey('Productos', models.DO_NOTHING)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carrito_items'


class Carritos(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    cliente = models.ForeignKey('Clientes', models.DO_NOTHING, blank=True, null=True)
    sesion_id = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    total_items = models.IntegerField(blank=True, null=True)
    total_precio = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carritos'


class Categorias(models.Model):
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.TextField(blank=True, null=True)
    color_hex = models.CharField(max_length=7, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categorias'


class Clientes(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    tipo_documento = models.CharField(max_length=10, blank=True, null=True)
    numero_documento = models.CharField(unique=True, max_length=20)
    nombre_completo = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(max_length=1, blank=True, null=True)
    es_empresa = models.BooleanField(blank=True, null=True)
    empresa_nombre = models.CharField(max_length=255, blank=True, null=True)
    puntos_fidelidad = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'


class Comprobantes(models.Model):
    venta = models.OneToOneField('Ventas', models.DO_NOTHING)
    numero_comprobante = models.CharField(unique=True, max_length=50)
    tipo_comprobante = models.CharField(max_length=20, blank=True, null=True)
    clave_acceso = models.CharField(max_length=100, blank=True, null=True)
    estado_sri = models.CharField(max_length=20, blank=True, null=True)
    contenido_pdf = models.BinaryField(blank=True, null=True)
    contenido_xml = models.BinaryField(blank=True, null=True)
    qr_code = models.TextField(blank=True, null=True)
    fecha_autorizacion = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'comprobantes'


class DispositivosMoviles(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
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
        managed = False
        db_table = 'dispositivos_moviles'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EmpresaConfig(models.Model):
    nombre_empresa = models.CharField(max_length=255)
    ruc = models.CharField(unique=True, max_length=20)
    direccion_fiscal = models.TextField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    moneda_base = models.CharField(max_length=10, blank=True, null=True)
    iva_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tasa_cambio_usd = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empresa_config'


class IaTrainingData(models.Model):
    fecha = models.DateField()
    categoria = models.ForeignKey(Categorias, models.DO_NOTHING, blank=True, null=True)
    ventas_totales = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_ventas = models.IntegerField()
    promedio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    clientes_unicos = models.IntegerField()
    productos_vendidos = models.IntegerField()
    dia_semana = models.IntegerField()
    es_fin_semana = models.BooleanField()
    mes = models.IntegerField()
    temporada = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ia_training_data'


class InventarioMovimientos(models.Model):
    producto = models.ForeignKey('Productos', models.DO_NOTHING)
    tipo_movimiento = models.CharField(max_length=20, blank=True, null=True)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    motivo = models.CharField(max_length=100, blank=True, null=True)
    referencia_id = models.IntegerField(blank=True, null=True)
    referencia_tipo = models.CharField(max_length=50, blank=True, null=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inventario_movimientos'


class ModeloIa(models.Model):
    nombre_modelo = models.CharField(max_length=100)
    algoritmo = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    modelo_serializado = models.BinaryField()
    metricas_entrenamiento = models.JSONField(blank=True, null=True)
    parametros_modelo = models.JSONField(blank=True, null=True)
    caracteristicas_usadas = models.TextField(blank=True, null=True)  # This field type is a guess.
    fecha_entrenamiento = models.DateTimeField()
    fecha_despliegue = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'modelo_ia'


class NotificacionPreferencias(models.Model):
    usuario = models.OneToOneField('Usuarios', models.DO_NOTHING)
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
        managed = False
        db_table = 'notificacion_preferencias'


class Notificaciones(models.Model):
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    dispositivo = models.ForeignKey(DispositivosMoviles, models.DO_NOTHING, blank=True, null=True)
    leida = models.BooleanField(blank=True, null=True)
    enviada = models.BooleanField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    error_envio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notificaciones'


class PrediccionesVentas(models.Model):
    modelo = models.ForeignKey(ModeloIa, models.DO_NOTHING)
    fecha_prediccion = models.DateField()
    categoria = models.ForeignKey(Categorias, models.DO_NOTHING, blank=True, null=True)
    monto_predicho = models.DecimalField(max_digits=12, decimal_places=2)
    intervalo_confianza = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'predicciones_ventas'


class ProductoPrecioHistorial(models.Model):
    producto = models.ForeignKey('Productos', models.DO_NOTHING)
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'producto_precio_historial'


class Productos(models.Model):
    sku = models.CharField(unique=True, max_length=100)
    codigo_barras = models.CharField(unique=True, max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categorias, models.DO_NOTHING)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    stock_maximo = models.IntegerField(blank=True, null=True)
    peso_kg = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    dimensiones = models.JSONField(blank=True, null=True)
    imagen_url = models.TextField(blank=True, null=True)
    etiquetas = models.TextField(blank=True, null=True)  # This field type is a guess.
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos'


class ReporteLogs(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    prompt_texto = models.TextField()
    tipo_salida = models.CharField(max_length=10)
    parametros_usados = models.JSONField(blank=True, null=True)
    resultado_query = models.JSONField(blank=True, null=True)
    archivo_url = models.TextField(blank=True, null=True)
    tiempo_ejecucion_ms = models.IntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reporte_logs'


class ReportePrompts(models.Model):
    nombre = models.CharField(max_length=100)
    prompt_texto = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    tipo_salida = models.CharField(max_length=10, blank=True, null=True)
    parametros = models.JSONField(blank=True, null=True)
    query_sql = models.TextField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    uso_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reporte_prompts'


class SincronizacionOffline(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    dispositivo = models.ForeignKey(DispositivosMoviles, models.DO_NOTHING, blank=True, null=True)
    tabla_modificada = models.CharField(max_length=50)
    registro_id = models.IntegerField()
    accion = models.CharField(max_length=10, blank=True, null=True)
    datos = models.JSONField()
    hash_datos = models.CharField(max_length=64)
    conflict_detected = models.BooleanField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    sincronizado = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sincronizacion_offline'


class TransaccionesPago(models.Model):
    venta = models.ForeignKey('Ventas', models.DO_NOTHING)
    metodo_pago = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, blank=True, null=True)
    transaccion_externa_id = models.CharField(max_length=100, blank=True, null=True)
    datos_transaccion = models.JSONField(blank=True, null=True)
    codigo_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    fecha_aprovisionamiento = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transacciones_pago'


class UserSessions(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey('Usuarios', models.DO_NOTHING)
    device_info = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    login_at = models.DateTimeField(blank=True, null=True)
    logout_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_sessions'


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
        managed = False
        db_table = 'usuarios'


class VentaDetalles(models.Model):
    venta = models.ForeignKey('Ventas', models.DO_NOTHING)
    producto = models.ForeignKey(Productos, models.DO_NOTHING)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venta_detalles'


class Ventas(models.Model):
    codigo_venta = models.CharField(unique=True, max_length=50)
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING)
    fecha_venta = models.DateTimeField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    iva = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, blank=True, null=True)
    metodo_pago = models.CharField(max_length=20, blank=True, null=True)
    transaccion_id = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    direccion_entrega = models.TextField(blank=True, null=True)
    tipo_entrega = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas'


class VoiceCommands(models.Model):
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, blank=True, null=True)
    comando_texto = models.TextField()
    comando_audio = models.BinaryField(blank=True, null=True)
    accion_ejecutada = models.CharField(max_length=100, blank=True, null=True)
    resultado = models.JSONField(blank=True, null=True)
    confianza = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    dispositivo = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'voice_commands'
