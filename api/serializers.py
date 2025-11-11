from rest_framework import serializers
from control.models import Cliente, Lectura, Lugar, Solicitud
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone

# ... (UserSerializer se mantiene igual) ...

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
    
        return super(UserSerializer, self).update(instance, validated_data)


# === VERSIÓN CORREGIDA DE LECTURASERIALIZER ===
class LecturaSerializer(serializers.ModelSerializer):
    # Hacemos que `created_by` sea de solo lectura.
    # Lo asignaremos automáticamente desde el usuario de la sesión en la vista.
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Hacemos que `lectura_anterior` también sea de solo lectura.
    # La calcularemos nosotros mismos en el método `create`.
    class Meta:
        model = Lectura
        fields = '__all__'
        read_only_fields = ('lectura_anterior',)

    def create(self, validated_data):
        """
        Sobrescribimos el método de creación para añadir nuestra lógica personalizada.
        """
        # 1. Obtenemos el cliente del request.
        cliente = validated_data['cliente']
        
        # 2. Determinamos la 'lectura_anterior' de forma segura en el servidor.
        if cliente.ultima_lectura:
            # Si el cliente ya tiene una lectura, usamos el valor de esa lectura.
            lectura_anterior = cliente.ultima_lectura.lectura
        else:
            # Si es la primera lectura, usamos el valor inicial de 'metros' del cliente.
            lectura_anterior = cliente.metros
        
        # 3. Añadimos los campos calculados a los datos a guardar.
        validated_data['lectura_anterior'] = lectura_anterior
        
        # El usuario se obtiene del 'contexto' que pasaremos desde la vista.
        validated_data['created_by'] = self.context['request'].user

        # 4. Creamos la nueva instancia de Lectura.
        lectura = Lectura.objects.create(**validated_data)
        

        # 5. ¡MUY IMPORTANTE! Actualizamos el cliente para que apunte a esta nueva lectura.
        cliente.ultima_lectura = lectura
        
        if cliente.created_at is None:
            cliente.created_at = timezone.now()
        
        cliente.save()
        
        return lectura

# ... (El resto de tus serializers se mantienen igual) ...

class ClienteSerializer(serializers.ModelSerializer):
    # La anidación aquí es correcta, ya que quieres ver los detalles
    # de la última lectura cuando obtienes un cliente.
    ultima_lectura = LecturaSerializer(read_only=True)
    class Meta:
        model = Cliente
        fields = '__all__'
        
class LecturaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lectura
        fields = ("id", "lectura", "fecha_lectura")

class ClienteListSerializer(serializers.ModelSerializer):
    # ultima_lectura es FK → la reducimos a lo mínimo que usa la lista
    ultima_lectura = LecturaMiniSerializer(read_only=True)

    class Meta:
        model = Cliente
        fields = (
            "id",
            "orden",           
            "lote",
            "nombre",
            "medidor",
            "metros",
            "ultima_lectura",
        )


class LugarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lugar
        fields = '__all__'

class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = '__all__'
