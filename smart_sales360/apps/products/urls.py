from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, ProductoPrecioHistorialViewSet

router = DefaultRouter()
router.register(r'products', ProductoViewSet, basename='products')
router.register(r'product-price-history', ProductoPrecioHistorialViewSet, basename='product-price-history')

urlpatterns = router.urls
