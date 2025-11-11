from django.contrib import admin

# Register your models here.
from .models import Cliente, Lectura, Lugar, Solicitud, Pago

admin.site.register(Cliente)
admin.site.register(Lectura)
admin.site.register(Lugar)
admin.site.register(Solicitud)
admin.site.register(Pago)
