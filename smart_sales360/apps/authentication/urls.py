from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet,
    UserSessionViewSet,
    DispositivoViewSet,
    NotificacionPreferenciasViewSet,
    NotificacionViewSet,
    LoginView,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'user-sessions', UserSessionViewSet, basename='user-sessions')
router.register(r'dispositivos', DispositivoViewSet, basename='dispositivos')
router.register(r'notificacion-preferencias', NotificacionPreferenciasViewSet, basename='notificacion-preferencias')
router.register(r'notificaciones', NotificacionViewSet, basename='notificaciones')

urlpatterns = router.urls + [
    path('login/', LoginView.as_view(), name='auth-login'),
]
