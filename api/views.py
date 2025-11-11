from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, filters
from control.models import *
from api.serializers import *
from django.contrib.auth.models import User
from control.utils import send_email, send_factura_email
from dateutil.relativedelta import relativedelta


class CustomBasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        user, auth = super().authenticate(request)
        
        if user:
            # Aqu铆 verificamos si el correo ya se ha enviado.
            if not hasattr(request, '_email_sent') or not request._email_sent:
                send_email(user)
                request._email_sent = True  # Marcamos que ya se envi贸 el correo

        return user, auth



class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', 'email')
    authentication_classes = [CustomBasicAuthentication]
    permission_classes = [IsAuthenticated]
    
class ClientePagination(PageNumberPagination):
    page_size = 50  # ajusta

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    pagination_class = ClientePagination
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    search_fields = ['nombre', 'lote']
    ordering_fields = ['orden', 'id', 'nombre', 'lote', 'medidor']  # 👈 nuevo

    def _is_paged(self, request):
        q = request.query_params
        paged = q.get('paged')
        return (paged in ("1", "true", "yes")) or ('page' in q) or ('page_size' in q)

    def get_serializer_class(self):
        if self.action == "list" and self._is_paged(self.request):
            return ClienteListSerializer
        return ClienteSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if self._is_paged(request):
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        qs = super().get_queryset()
        lugar_nombre = self.request.query_params.get('lugar_nombre')
        if lugar_nombre:
            qs = qs.filter(lugar__nombre__icontains=lugar_nombre)
        medidor = self.request.query_params.get('medidor')
        if medidor:
            qs = qs.filter(medidor__icontains=medidor)
        ordering = self.request.query_params.get('ordering')
        if ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('orden', 'id')  # orden estable
        return qs



class LecturaViewSet(viewsets.ModelViewSet):
    queryset = Lectura.objects.all()
    serializer_class = LecturaSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        lectura = serializer.save()

        consumo_total = lectura.lectura - lectura.lectura_anterior
        valor = lectura.cliente.lugar.valor
        total_pagar = consumo_total * valor
        fecha_vencimiento = lectura.fecha_lectura + relativedelta(months=1)

        # Enviar correo cuando se crea una nueva lectura
        send_factura_email(lectura.cliente, lectura, None, total_pagar, fecha_vencimiento, consumo_total, valor)

    def perform_update(self, serializer):
        lectura = serializer.save()

        consumo_total = lectura.lectura - lectura.lectura_anterior
        valor = lectura.cliente.lugar.valor
        total_pagar = consumo_total * valor
        fecha_vencimiento = lectura.fecha_lectura + relativedelta(months=1)

        # Enviar correo cuando se actualiza una lectura existente
        send_factura_email(lectura.cliente, lectura, None, total_pagar, fecha_vencimiento, consumo_total, valor)


class LugarViewSet(viewsets.ModelViewSet):
    queryset = Lugar.objects.all()
    serializer_class = LugarSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


class SolicitudViewSet(viewsets.ModelViewSet):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        cliente = self.request.query_params.get('cliente')
        if cliente:
            qs = qs.filter(cliente_id=cliente)

        estado = self.request.query_params.get('estado')
        if estado is not None:
            estado_bool = str(estado).lower() in ('true', '1', 't')
            qs = qs.filter(estado=estado_bool)

        ordering = self.request.query_params.get('ordering')
        if ordering in ('created_at', '-created_at'):
            qs = qs.order_by(ordering)

        return qs