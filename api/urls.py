from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'lecturas', views.LecturaViewSet)
router.register(r'lugares', views.LugarViewSet)
router.register(r'solicitudes', views.SolicitudViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
