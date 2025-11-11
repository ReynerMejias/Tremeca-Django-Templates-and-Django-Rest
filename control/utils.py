from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging 


def registerLogEntry(request, obj, action_flag, change_message):
    LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=change_message,
    )

logger = logging.getLogger(__name__)

def send_email(user):
    try:
        subject = 'Inicio de sesion exitoso'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]

        # Contenido del correo en HTML
        html_content = render_to_string('login_email.html', {'user': user})

        msg = EmailMultiAlternatives(subject, '', from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(f'Error al enviar correo electronico a {user.email}: {e}')

def send_new_user_email(user, temporal_password):
    try:
        subject = 'Bienvenido a la plataforma'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]

        html_content = render_to_string('usuarionuevo_email.html', {'user': user, 'password': temporal_password})

        msg = EmailMultiAlternatives(subject, '', from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(f'Error al enviar correo de bienvenida a {user.email}: {e}')


def send_edit_user_email(user):
    try:
        subject = 'Actualizacion de datos de usuario'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]

        html_content = render_to_string('editarUsuario_email.html', {'user': user})

        msg = EmailMultiAlternatives(subject, '', from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(f'Error al enviar correo de actualizacion a {user.email}: {e}')


def send_factura_email(user, lectura, pago, total_pagar, fecha_vencimiento, consumo_total, valor):
    try:
        subject = 'Pago de factura recibido' if lectura.pago else 'Recibo de factura pendiente'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.correo]

        html_content = render_to_string('factura_correo.html', {
            'user': user,
            'lectura': lectura,
            'pago': pago,
            'total_pagar': total_pagar,
            'fecha_vencimiento': fecha_vencimiento,
            'consumo_total': consumo_total,
            'valor': valor,
            'moratorio': lectura.moratorio,
            'observacion': lectura.observacion
        })

        text_content = f'Estimado {user.nombre}, su factura ha sido generada.'

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

    except Exception as e:
        logger.error(f'Error al enviar correo de factura a {user.correo}: {e}')

