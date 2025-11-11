from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

# Create your models here.
class Cliente(models.Model):
    orden = models.IntegerField()
    lote = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    medidor = models.CharField(max_length=20, unique=True, blank=True, null=True)
    metros = models.IntegerField(default=0, validators=[MinValueValidator(0)], null=True, blank=True)
    ultima_lectura = models.ForeignKey('Lectura', on_delete=models.SET_NULL, null=True, blank=True, related_name='ultima_cliente')
    lugar = models.ForeignKey('Lugar', on_delete=models.CASCADE, related_name='clientes')
    correo = models.EmailField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.lote} - {self.nombre}'
    

class Lectura(models.Model):
    lectura = models.IntegerField(default=0)
    lectura_anterior = models.IntegerField(default=0)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE,  related_name='lecturas', null=True, blank=True)
    fecha_lectura = models.DateField(auto_now=False, auto_now_add=False)
    pago = models.OneToOneField('Pago', on_delete=models.SET_NULL, null=True, blank=True, related_name='lecturas')
    moratorio = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    observacion = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='lecturas', blank=True, null=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.lectura}  ({self.created_at})'
    

class Pago(models.Model):
    valor = models.IntegerField()
    fecha_pago = models.DateField(auto_now=False, auto_now_add=False)
    tipo_pago = models.CharField(max_length=20)
    lectura = models.OneToOneField(Lectura, on_delete=models.CASCADE, null=True, blank=True, related_name='pago_relacionado')
    observacion = models.TextField(blank=True, null=True, max_length=15)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.fecha_pago)
    

class Lugar(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    dia = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(31)])
    valor = models.IntegerField(default=350)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre
    
    
class Solicitud(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=50)
    descripcion = models.TextField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.cliente.lote}  ({self.created_at})'