from rest_framework.routers import DefaultRouter
from .views import EmpresaConfigViewSet

router = DefaultRouter()
router.register(r'', EmpresaConfigViewSet, basename='empresa')

urlpatterns = router.urls
