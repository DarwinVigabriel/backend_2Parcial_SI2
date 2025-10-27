from rest_framework.routers import DefaultRouter
from .views import InventarioMovimientosViewSet

router = DefaultRouter()
router.register(r'', InventarioMovimientosViewSet, basename='inventario_movil')

urlpatterns = router.urls
