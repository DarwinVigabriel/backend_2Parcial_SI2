from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet, CartItemViewSet, VentaViewSet, PagoViewSet,
    VentaComprobantePDFViewSet, VentaHistoricoViewSet, VentaDashboardViewSet,
    DispositivoMovilViewSet, VentaMovilViewSet, NotificacionPushViewSet,
    ReporteViewSet
)

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='carts')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')
router.register(r'ventas', VentaViewSet, basename='ventas')
router.register(r'pagos', PagoViewSet, basename='pagos')
router.register(r'comprobante', VentaComprobantePDFViewSet, basename='comprobante')
router.register(r'historico', VentaHistoricoViewSet, basename='historico')
router.register(r'dashboard', VentaDashboardViewSet, basename='dashboard')
# CU17-19: Endpoints móvil
router.register(r'dispositivos-movil', DispositivoMovilViewSet, basename='dispositivos-movil')
router.register(r'ventas-movil', VentaMovilViewSet, basename='ventas-movil')
# CU20: Notificaciones push
router.register(r'notificaciones', NotificacionPushViewSet, basename='notificaciones')
# CU21-23: Reportes dinámicos
router.register(r'reportes', ReporteViewSet, basename='reportes')

urlpatterns = router.urls