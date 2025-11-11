from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.control, name='control'),
    
    path('login/', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('editarPerfil/', views.editarPerfil, name='editarPerfil'),

    path('lugares/', views.lugares, name='lugares'),
    path('lugares/editar/orden/<str:codigo>/', views.ordenLugar, name='ordenLugar'),
    path('lugares/crearLugar/', views.crearLugar, name='crearLugar'),
    path('lugares/editar/<str:codigo>/', views.editarLugar, name='editarLugar'),
    path('lugares/eliminar/<str:id>/', views.eliminarLugar, name='eliminarLugar'),

    path('clientes/', views.clientes, name='clientes'),
    path('clientes/crearCliente/', views.crearCliente, name='crearCliente'),
    path('clientes/editarCliente/<str:cliente>/', views.editarCliente, name='editarCliente'),
    path('clientes/eliminarCliente/<str:cliente>/', views.eliminarCliente, name='eliminarCliente'),
    
    path('lecturas/', views.lecturas, name='lecturas'),
    path('lecturas/lectura/<str:lectura>/', views.lectura, name='lectura'),
    path('lecturas/lectura_recibo_print/<int:id>/', views.imprimir_lectura, name='lectura_recibo_print'),
    path('lecturas/editarLectura/<str:lectura>/', views.editarLectura, name='editarLectura'),
    path('lecturas/eliminarLectura/<str:lectura>/', views.eliminarLectura, name='eliminarLectura'),

    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/crearUsuario/', views.crearUsuario, name='crearUsuario'),
    path('usuarios/editarUsuario/<str:usuario>/', views.editarUsuario, name='editarUsuario'),
    path('usuarios/eliminarUsuario/<str:usuario>/', views.eliminarUsuario, name='eliminarUsuario'),

    path('grupos/', views.grupos, name='grupos'),
    path('grupos/crearGrupo/', views.crearGrupo, name='crearGrupo'),
    path('grupos/editarGrupo/<str:grupo>/', views.editarGrupo, name='editarGrupo'),
    path('grupos/eliminarGrupo/<str:grupo>/', views.eliminarGrupo, name='eliminarGrupo'),

    path('solicitudes/', views.solicitudes, name='solicitudes'),
    path('solicitudes/solicitud/<str:solicitud>', views.solicitud, name='solicitud'),
    path('solicitudes/crearSolicitud/', views.crearSolicitud, name='crearSolicitud'),
    path('buscar-clientes/', views.buscarClientes, name='buscarClientes'),

    path('historial/', views.historial, name='historial'),
    path('estado/', views.estado, name='estado'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = 'control.views.error_404'
handler500 = 'control.views.error_500'
handler403 = 'control.views.error_403'