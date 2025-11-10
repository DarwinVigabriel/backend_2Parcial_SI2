from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet, CartItemViewSet, VentaViewSet, PagoViewSet,
    VentaComprobantePDFViewSet, VentaHistoricoViewSet, VentaDashboardViewSet
)

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='carts')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')
router.register(r'ventas', VentaViewSet, basename='ventas')
router.register(r'pagos', PagoViewSet, basename='pagos')
router.register(r'comprobante', VentaComprobantePDFViewSet, basename='comprobante')
router.register(r'historico', VentaHistoricoViewSet, basename='historico')
router.register(r'dashboard', VentaDashboardViewSet, basename='dashboard')

urlpatterns = router.urls
