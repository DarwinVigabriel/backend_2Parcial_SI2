from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CartItemViewSet, VentaViewSet, PagoViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='carts')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')
router.register(r'ventas', VentaViewSet, basename='ventas')
router.register(r'pagos', PagoViewSet, basename='pagos')

urlpatterns = router.urls
