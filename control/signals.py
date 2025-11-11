from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Lectura
from django.db.models.signals import post_save
from .utils import send_email

@receiver(user_logged_in)
def send_login_email(sender, request, user, **kwargs):
    send_email(user)
    

@receiver(post_save, sender=Lectura)
def actualizar_ultima_lectura(sender, instance, created, **kwargs):
    """Actualiza la última lectura de un cliente solo cuando se crea una nueva."""
    if created:  # Solo si es una lectura nueva
        instance.cliente.ultima_lectura = instance
        instance.cliente.save(update_fields=["ultima_lectura"])
