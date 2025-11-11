from datetime import date
import datetime
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from .models import Cliente, Lectura, Lugar, Solicitud, Pago
from .utils import registerLogEntry, send_new_user_email, send_edit_user_email, send_factura_email
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib.auth.models import User, Group, Permission
from django.db.models.functions import Lower
from django.contrib.admin.models import LogEntry
from django.shortcuts import get_object_or_404, redirect, render
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.utils.dateparse import parse_date
import random
import logging

logger = logging.getLogger(__name__)


@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def loginView(request):
    was_limited = getattr(request, 'limited', False)

    if was_limited:
        return render(request, 'login.html', {"error": "Demasiados intentos, intente de nuevo en 1 minuto."})

    if request.user.is_authenticated:
        return redirect('control')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user) 
            return redirect('control')
        else:
            return render(request, 'login.html')
        
    return render(request, 'login.html')



@login_required(login_url='login')
def logoutView(request):
    logout(request)
    return redirect('login')



@login_required(login_url='login')
def editarPerfil(request):
    if request.method == 'POST':
        request.user.username = request.POST['username']
        request.user.first_name = request.POST['first_name']
        request.user.last_name = request.POST['last_name']
        request.user.email = request.POST['email']

        if request.POST['password'] != '':
            request.user.set_password(request.POST['password'])

        request.user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        send_edit_user_email(request.user)

        return redirect('control')

    context = {
        "usuario": request.user
    }

    return render(request, 'editarPerfil.html', context)



@login_required(login_url='login')
def control(request):

    context = {
        "apk_url": getattr(settings, "MOBILE_APK_URL", ""),   # ej: https://tusitio.com/builds/tremeca-latest.apk
        "play_url": getattr(settings, "MOBILE_PLAY_URL", ""), # opcional
    }

    return render(request, 'control.html', context)



@login_required(login_url='login')
def lecturas(request):
    user = request.user
    query = request.GET.get('q')
    estado = request.GET.get('estado', 'pendientes')
    lugar_actual = request.GET.get('lugar', 'todos')
    cantidades_por_pagina = [10, 20, 50, 100, 500]
    per_page = int(request.GET.get('per_page', 15))

    if user.is_superuser or user.is_staff:
        lugares = Lugar.objects.all()
        lecturas_list = Lectura.objects.all()
    else:
        grupos = user.groups.filter(name__startswith="Cajero ")
        nombres_lugares = [g.name.replace("Cajero ", "") for g in grupos]
        lugares = Lugar.objects.filter(nombre__in=nombres_lugares)
        lecturas_list = Lectura.objects.filter(cliente__lugar__nombre__in=nombres_lugares)

    # Si solo tiene acceso a un lugar, se usa automáticamente y se oculta el filtro
    mostrar_filtro_lugar = True
    if lugares.count() == 1:
        lugar_unico = lugares.first()
        lugar_actual = str(lugar_unico.id)
        mostrar_filtro_lugar = False

    # Filtro por lugar específico
    if lugar_actual != "todos":
        lecturas_list = lecturas_list.filter(cliente__lugar__id=lugar_actual)

    # Filtro de búsqueda
    if query and query != 'None':
        lecturas_list = lecturas_list.filter(
            Q(cliente__nombre__icontains=query) |
            Q(cliente__lote__icontains=query)
        )

    # Excluir lecturas sin consumo
    lecturas_list = lecturas_list.exclude(lectura_anterior=F('lectura'))

    # Ordenar por estado de pago y fecha
    lecturas_list = lecturas_list.order_by('pago', 'fecha_lectura')

    # Contar pendientes
    lecturas_pendientes = lecturas_list.filter(pago__isnull=True).count()

    # Filtrar por estado
    if estado == 'pendientes':
        lecturas_list = lecturas_list.filter(pago__isnull=True)
    elif estado == 'pagadas':
        lecturas_list = lecturas_list.filter(pago__isnull=False)

    # Paginación
    paginator = Paginator(lecturas_list, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
        "estado_actual": estado,
        "lugares": lugares if mostrar_filtro_lugar else None,
        "lugar_actual": lugar_actual,
        "cantidades_por_pagina": cantidades_por_pagina,
        "per_page_actual": per_page,
        "lecturas_pendientes": lecturas_pendientes,
        "mostrar_estado": True,
    }

    return render(request, 'lecturas.html', context)




@login_required(login_url='login')
@permission_required('control.change_lectura', raise_exception=True)
def lectura(request, lectura):
    lectura = Lectura.objects.get(id=lectura)

    consumo_total = lectura.lectura - lectura.lectura_anterior
    valor = lectura.cliente.lugar.valor
    total_pagar = (consumo_total * valor) + lectura.moratorio
    fecha_vencimiento = lectura.fecha_lectura + relativedelta(months=1)

    if request.method == 'POST':
        form_tipo = request.POST.get('form_tipo', None)

        # FORM 1: Guardar moratorio y observación
        if form_tipo == 'moratorio':
            try:
                nuevo_moratorio = request.POST.get('moratorio', '0')
                observacion = request.POST.get('observacion', '')
                lectura.moratorio = int(nuevo_moratorio) if nuevo_moratorio.isdigit() else 0
                lectura.observacion = observacion
                lectura.save()
                messages.success(request, 'Moratorio actualizado correctamente.')
            except Exception as e:
                logger.error(f'Error al actualizar moratorio: {e}')
                messages.error(request, "Error al actualizar el moratorio.")
            return redirect('lectura', lectura=lectura.id)

        # FORM 2: Registrar el pago
        elif form_tipo == 'pago':
            fecha_pago = request.POST.get('fecha_pago')
            valor_pago = request.POST.get('valor')
            tipo_pago = request.POST.get('tipo_pago')
            observacion = request.POST.get('comprobante')

            try:
                pago = Pago.objects.create(
                    valor=valor_pago,
                    fecha_pago=fecha_pago,
                    tipo_pago=tipo_pago,
                    observacion=observacion,
                    created_by=request.user,
                    lectura=lectura
                )
                lectura.pago = pago
                lectura.save()
                messages.success(request, 'Lectura actualizada exitosamente.')
                send_factura_email(lectura.cliente, lectura, pago, total_pagar, fecha_vencimiento, consumo_total, valor)
                messages.success(request, "Pago registrado y correo enviado con éxito.")
            except Exception as e:
                logger.error(f'Error al procesar el pago: {e}')
                messages.error(request, "Hubo un error al procesar el pago o enviar el correo.")
            return redirect('lectura', lectura=lectura.id)

        # FORM 3: Actualizar correo
        elif form_tipo == 'correo':
            correo = request.POST.get('correo')
            if correo:
                lectura.cliente.correo = correo
                lectura.cliente.save()
                messages.success(request, 'Correo actualizado correctamente.')
            return redirect('lectura', lectura=lectura.id)

    context = {
        "lectura": lectura,
        "consumo_total": consumo_total,
        "total_pagar": total_pagar,
        "valor": valor,
        "fecha_vencimiento": fecha_vencimiento,
        "today": date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'lectura.html', context)


@login_required(login_url='login')
@permission_required('control.view_lectura', raise_exception=True)
def imprimir_lectura(request, id):
    lectura = get_object_or_404(Lectura, pk=id)
    consumo_total = lectura.lectura - lectura.lectura_anterior
    if lectura.moratorio:
        total_pagar = consumo_total * lectura.cliente.lugar.valor + lectura.moratorio
    else:
        total_pagar = consumo_total * lectura.cliente.lugar.valor
    fecha_vencimiento = lectura.fecha_lectura + relativedelta(months=1)

    return render(request, 'lectura_recibo_print.html', {
        'lectura': lectura,
        'consumo_total': consumo_total,
        'total_pagar': total_pagar,
        'fecha_vencimiento': fecha_vencimiento
    })


@login_required(login_url='login')
@permission_required('control.delete_lectura', raise_exception=True)
def eliminarLectura(request, lectura):
    lectura = Lectura.objects.get(id=lectura)
    lectura.delete()
    messages.success(request, 'Lectura eliminada correctamente.')

    registerLogEntry(request, lectura, 3, 'Lectura eliminada')

    return redirect('lecturas')




@login_required(login_url='login')
@permission_required('control.change_lectura', raise_exception=True)
def editarLectura(request, lectura):
    # Obtiene la instancia de Lectura, o devuelve un 404 si no existe
    lectura = get_object_or_404(Lectura, id=lectura)

    if request.method == 'POST':
        try:
            # Actualiza los campos con los datos enviados
            lectura.lectura = request.POST.get('lectura', lectura.lectura)
            
            # Maneja la foto solo si se ha subido una nueva
            if 'foto' in request.FILES:
                lectura.foto = request.FILES['foto']
            
            # Guarda los cambios
            lectura.save()
            messages.success(request, 'Lectura actualizada exitosamente.')

            # Registra el evento en el log
            registerLogEntry(request, lectura, 2, 'Lectura editada')

            # Mensaje de éxito
            messages.success(request, "Lectura actualizada exitosamente.")
            return redirect('lecturas')

        except Exception as e:
            # Mensaje de error en caso de fallo
            messages.error(request, f"Error al actualizar la lectura: {str(e)}")
    
    # Contexto para la plantilla
    context = {
        "lectura": lectura
    }

    return render(request, 'editarLectura.html', context)



@login_required(login_url='login')
@permission_required('control.view_cliente', raise_exception=True)
def clientes(request):
    user = request.user
    query = request.GET.get('q')
    lugar_filter = request.GET.get('lugar')
    per_page = request.GET.get('per_page', 15)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 15

    # Obtener lugares permitidos
    if user.is_superuser or user.is_staff:
        lugares = Lugar.objects.all().order_by('nombre')
        clientes_list = Cliente.objects.all()
    else:
        grupos = user.groups.filter(name__startswith="Cajero ")
        nombres_lugares = [g.name.replace("Cajero ", "") for g in grupos]
        lugares = Lugar.objects.filter(nombre__in=nombres_lugares).order_by('nombre')
        clientes_list = Cliente.objects.filter(lugar__nombre__in=nombres_lugares)

    # Si solo tiene un lugar, se selecciona automáticamente y se oculta el filtro
    mostrar_filtro_lugar = True
    if lugares.count() == 1:
        lugar_unico = lugares.first()
        lugar_filter = str(lugar_unico.id)
        mostrar_filtro_lugar = False

    # Filtro por texto
    if query and query != 'None':
        clientes_list = clientes_list.filter(
            Q(nombre__icontains=query) |
            Q(lote__icontains=query)
        )

    # Filtro por lugar
    if lugar_filter and lugar_filter != 'todos':
        clientes_list = clientes_list.filter(lugar_id=lugar_filter)

    # Ordenamiento
    clientes_list = clientes_list.order_by('lugar__nombre', 'orden')

    # Paginación
    paginator = Paginator(clientes_list, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
        "lugar_actual": lugar_filter,
        "per_page_actual": per_page,
        "lugares": lugares if mostrar_filtro_lugar else None,
        "cantidades_por_pagina": [10, 20, 50, 100, 200, 500],
    }

    return render(request, 'clientes.html', context)

    
    
@login_required(login_url='login')
@permission_required('control.delete_cliente', raise_exception=True)
def eliminarCliente(request, cliente):
    cliente = Cliente.objects.get(id=cliente)
    cliente.delete()
    messages.success(request, 'Cliente eliminado correctamente.')

    registerLogEntry(request, cliente, 3, 'Cliente eliminado')

    return redirect('clientes')




@login_required(login_url='login')
@permission_required('control.add_cliente', raise_exception=True)
def crearCliente(request):

    if request.method == 'POST':
        lote = request.POST['lote']
        nombre = request.POST['nombre']
        medidor = request.POST['medidor']
        lugar_id = request.POST['lugar']
        correo = request.POST['correo']
        metros = request.POST.get('metros')

        # Validar que metros y lugar_id estén presentes
        if not metros or not lugar_id:
            messages.error(request, 'Debe ingresar los metros y seleccionar el grupo/lugar.')
            return render(request, 'crearCliente.html', {"lugares": Lugar.objects.all()})

        lugar = Lugar.objects.get(id=lugar_id)
        
        try:
            orden = Cliente.objects.filter(lugar=lugar).order_by('orden').last().orden + 1
        except:
            orden = 1

        cliente = Cliente(lote=lote, nombre=nombre, medidor=medidor, lugar=lugar, orden=orden, correo=correo, metros=metros)
        cliente.save()
        messages.success(request, 'Datos del cliente actualizados.')
        messages.success(request, 'Cliente creado exitosamente.')

        registerLogEntry(request, cliente, 1, 'Cliente creado')

        return redirect('clientes')

    return render(request, 'crearCliente.html', {"lugares": Lugar.objects.all()})


@login_required(login_url='login')
@permission_required('control.change_cliente', raise_exception=True)
def editarCliente(request, cliente):

    cliente = Cliente.objects.get(id=cliente)

    if request.method == 'POST':
        cliente.lote = request.POST['lote']
        cliente.nombre = request.POST['nombre']
        cliente.medidor = request.POST['medidor']
        cliente.lugar = Lugar.objects.get(id=request.POST['lugar'])
        cliente.correo = request.POST['correo']

        # Si no hay lectura previa, usar metros-inicial del formulario
        if not cliente.ultima_lectura:
            cliente.metros = request.POST.get('metros-inicial', cliente.metros)

        cliente.save()
        messages.success(request, 'Datos del cliente actualizados.')

        registerLogEntry(request, cliente, 2, 'Cliente editado')

        return redirect('clientes')

    context = {
        "cliente": cliente,
        "lugares": Lugar.objects.all()
    }

    return render(request, 'editarCliente.html', context)




@login_required(login_url='login')
@permission_required('control.view_lugar', raise_exception=True)
def lugares(request):
    query = request.GET.get('q')

    if query and query != 'None':  # Si hay un término de búsqueda
        lugares_list = Lugar.objects.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query)).order_by('nombre')
    else:
        lugares_list = Lugar.objects.all().order_by('nombre')
        
    # Asignando el atributo `has_clients` para saber si un lugar tiene clientes
    for lugar in lugares_list:
        lugar.has_clients = lugar.clientes.exists()

    paginator = Paginator(lugares_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        "page_obj": page_obj,
        "query": query,
    }

    return render(request, 'lugares.html', context)



@login_required(login_url='login')
@permission_required('control.add_lugar', raise_exception=True)
def crearLugar(request):

    if request.method == 'POST':
        nombre = request.POST['lugar']
        codigo = request.POST['codigo']
        dia = request.POST['dia']
        valor = request.POST['valor']

        lugar = Lugar(nombre=nombre, codigo=codigo, dia=dia, valor=valor)
        lugar.save()
        messages.success(request, 'Orden de clientes actualizado correctamente.')
        messages.success(request, 'Lugar actualizado con éxito.')
        messages.success(request, 'Lugar creado correctamente.')

        registerLogEntry(request, lugar, 1, 'Lugar creado')

        return redirect('lugares')

    return render(request, 'crearLugar.html')

@login_required(login_url='login')
@permission_required('control.change_lugar', raise_exception=True)
def editarLugar(request, codigo):

    lugar = Lugar.objects.get(codigo=codigo)

    if request.method == 'POST':
        lugar.nombre = request.POST['lugar']
        lugar.codigo = request.POST['codigo']
        lugar.dia = request.POST['dia']
        lugar.valor = request.POST['valor']
        lugar.save()
        messages.success(request, 'Orden de clientes actualizado correctamente.')
        messages.success(request, 'Lugar actualizado con éxito.')

        registerLogEntry(request, lugar, 2, 'Lugar editado')

        return redirect('lugares')

    context = {
        "lugar": lugar
    }

    return render(request, 'editarLugar.html', context)

@login_required(login_url='login')
@permission_required('control.delete_lugar', raise_exception=True)
def eliminarLugar(request, id):
    lugar = Lugar.objects.get(id=id)
    lugar.delete()
    messages.success(request, 'Lugar eliminado exitosamente.')

    registerLogEntry(request, lugar, 3, 'Lugar eliminado')

    return redirect('lugares')

@login_required(login_url='login')
@permission_required('control.change_lugar', raise_exception=True)
def ordenLugar(request, codigo):
    lugar = Lugar.objects.get(codigo=codigo)

    if request.method == 'POST':
        for cliente in Cliente.objects.filter(lugar=lugar):
            cliente.orden = request.POST[f'order_{cliente.id}']

            cliente.save()

        registerLogEntry(request, lugar, 2, 'Orden de clientes editado')

        return redirect('editarLugar', codigo=codigo)



    context = {
        "lugar": lugar,
        "clientes": Cliente.objects.filter(lugar=lugar).order_by('orden'),
    }

    return render(request, 'ordenLugar.html', context)


@login_required(login_url='login')
@permission_required('control.view_user', raise_exception=True)
def usuarios(request):
    query = request.GET.get('q')

    if query and query != 'None':  # Si hay un término de búsqueda
        usuarios_list = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).order_by('username')
    else:
        usuarios_list = User.objects.all().order_by('username')

    paginator = Paginator(usuarios_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,  # Para mantener el término de búsqueda
    }

    return render(request, 'usuarios.html', context)




@login_required(login_url='login')
@permission_required('control.add_user', raise_exception=True)
def crearUsuario(request):
    if request.method == 'POST':
        # Captura los datos del formulario
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        temporal_password = f"{first_name[0].lower()}{last_name.lower()}{random.randint(10,99)}"

        # Captura el grupo seleccionado
        group_id = request.POST.get('groups')

        # Obtén si el usuario estará activo
        is_active = request.POST.get('is_active', 0)  # Por defecto 0 si no está marcado
        is_active = bool(int(is_active))

        # Obtén si el usuario es superusuario
        is_superuser = request.POST.get('is_staff', 0)  # Por defecto 0 si no está marcado
        is_superuser = bool(int(is_superuser))

        # Crea el usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=temporal_password,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_active = is_active

        if is_superuser:  # Administrador
            user.is_staff = True
            user.is_superuser = True


        try:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
        except Group.DoesNotExist:
            pass  # Si el grupo no existe, no hacer nada

        user.save()
        messages.success(request, 'Usuario creado y correo enviado.')
        send_new_user_email(user, temporal_password)  # Enviar correo de bienvenida al nuevo usuario

        registerLogEntry(request, user, 1, 'Usuario creado')

        return redirect('usuarios')  # Redirige a la página de usuarios

    # Contexto para renderizar el formulario
    context = {
        "groups": Group.objects.all()  # Pasa los grupos al template
    }
    return render(request, 'crearUsuario.html', context)





@login_required(login_url='login')
@permission_required('control.change_user', raise_exception=True)
def editarUsuario(request, usuario):

    usuario = User.objects.get(id=usuario)

    if request.method == 'POST':
        usuario.username = request.POST['username']
        usuario.first_name = request.POST['first_name']
        usuario.last_name = request.POST['last_name']
        usuario.email = request.POST['email']
        usuario.is_active = bool(int(request.POST.get('is_active', 0)))
        
        group_id = request.POST.get('groups')

        try:
            group = Group.objects.get(id=group_id)
            usuario.groups.clear()
            usuario.groups.add(group)
        except Group.DoesNotExist:
            pass

        usuario.save()
        messages.success(request, 'Usuario editado correctamente.')

        registerLogEntry(request, usuario, 2, 'Usuario editado')

        return redirect('usuarios')

    context = {
        "usuario": usuario,
        "groups": Group.objects.all(),
    }

    return render(request, 'editarUsuario.html', context)

@login_required(login_url='login')
@permission_required('control.delete_user', raise_exception=True)
def eliminarUsuario(request, usuario):
    usuario = User.objects.get(id=usuario)
    usuario.delete()
    messages.success(request, 'Usuario eliminado exitosamente.')

    registerLogEntry(request, usuario, 3, 'Usuario eliminado')

    return redirect('usuarios')


@login_required(login_url='login')
@permission_required('control.view_solicitud', raise_exception=True)
def solicitudes(request):
    query = request.GET.get('q')

    if query and query != 'None':
        solicitudes_list = Solicitud.objects.filter(Q(titulo__icontains=query) | Q(descripcion__icontains=query)).order_by('-created_at')
    else:
        solicitudes_list = Solicitud.objects.all().order_by('-created_at')

    paginator = Paginator(solicitudes_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,  # Para mantener el término de búsqueda
    }

    return render(request, 'solicitudes.html', context)


@login_required(login_url='login')
@permission_required('control.change_solicitud', raise_exception=True)
def solicitud(request, solicitud):

    solicitud = Solicitud.objects.get(id=solicitud)

    if request.method == 'POST':
        solicitud.estado = True
        solicitud.save()
        messages.success(request, 'Solicitud marcada como atendida.')

        return redirect('solicitudes')

    context = {
        "solicitud": solicitud
    }

    return render(request, 'solicitud.html', context)



@login_required
def buscarClientes(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(
        Q(nombre__icontains=q) |
        Q(medidor__icontains=q) |
        Q(lote__icontains=q)
    )[:15]  # Limitar resultados

    results = [
        {"id": c.id, "text": f"{c.nombre} / {c.lugar} / {c.lote}"}
        for c in clientes
    ]
    return JsonResponse({"results": results})





@login_required(login_url='login')
@permission_required('control.add_solicitud', raise_exception=True)
def crearSolicitud(request):
    if request.method == 'POST':
        titulo = request.POST['titulo']
        descripcion = request.POST['descripcion']
        cliente_id = request.POST.get('cliente')

        if not cliente_id or not cliente_id.isdigit():
            messages.error(request, "Debe seleccionar un cliente válido.")
            return redirect('crearSolicitud')

        cliente = get_object_or_404(Cliente, id=cliente_id)

        Solicitud.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            usuario=request.user,
            cliente=cliente
        )
        messages.success(request, 'Solicitud creada exitosamente.')
        messages.success(request, "Solicitud creada exitosamente.")
        return redirect('control')

    return render(request, 'crearSolicitud.html')




@login_required(login_url='login')
@permission_required('control.view_group', raise_exception=True)
def grupos(request):
    query = request.GET.get('q')

    if query and query != 'None':
        grupos_list = Group.objects.filter(Q(name__icontains=query)).order_by('name')
    else:
        grupos_list = Group.objects.all().order_by('name')

    paginator = Paginator(grupos_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,  # Para mantener el término de búsqueda
    }

    return render(request, 'grupos.html', context)


@login_required(login_url='login')
@permission_required('control.add_group', raise_exception=True)
def crearGrupo(request):
    if request.method == 'POST':
        name = request.POST['nombre']
        permissions = request.POST.getlist('permisos')

        group = Group(name=name)
        group.save()
        messages.success(request, 'Grupo creado exitosamente.')

        for permission in permissions:
            group.permissions.add(permission)

        registerLogEntry(request, group, 1, 'Grupo creado')

        return redirect('grupos')
    
    context = {
        "permisos": Permission.objects.all()
    }

    return render(request, 'crearGrupo.html', context)


@login_required(login_url='login')
@permission_required('control.change_group', raise_exception=True)
def editarGrupo(request, grupo):
    grupo = Group.objects.get(id=grupo)

    if request.method == 'POST':
        grupo.name = request.POST['nombre']
        permissions = request.POST.getlist('permisos')

        for permission in Permission.objects.all():
            if str(permission.id) in permissions:
                grupo.permissions.add(permission)
            else:
                grupo.permissions.remove(permission)

        grupo.save()
        messages.success(request, 'Grupo actualizado correctamente.')

        registerLogEntry(request, grupo, 2, 'Grupo editado')

        return redirect('grupos')

    context = {
        "grupo": grupo,
        "permisos": Permission.objects.all(),
        "permisos_grupo": grupo.permissions.values_list('id', flat=True)
    }

    return render(request, 'editarGrupo.html', context)


@login_required(login_url='login')
@permission_required('control.delete_group', raise_exception=True)
def eliminarGrupo(request, grupo):
    grupo = Group.objects.get(id=grupo)
    grupo.delete()
    messages.success(request, 'Grupo eliminado exitosamente.')

    registerLogEntry(request, grupo, 3, 'Grupo eliminado')

    return redirect('grupos')


@login_required(login_url='login')
@permission_required('control.view_logentry', raise_exception=True)
def historial(request):
    logs = LogEntry.objects.all().order_by('-action_time')

    paginator = Paginator(logs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }

    return render(request, 'historial.html', context)



from django.contrib.auth.models import User

@login_required(login_url='login')
@permission_required('control.view_pago', raise_exception=True)
def estado(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    usuario_id = request.GET.get('usuario')
    per_page = request.GET.get('per_page', 200)

    pagos = Pago.objects.all().order_by('-fecha_pago')


    if usuario_id:
        pagos = pagos.filter(created_by__id=usuario_id)

    # Validar y aplicar el filtro de fechas
    if fecha_inicio and fecha_fin:
        fecha_inicio_parsed = parse_date(fecha_inicio)
        fecha_fin_parsed = parse_date(fecha_fin)

        if fecha_inicio_parsed and fecha_fin_parsed:
            if fecha_inicio_parsed <= fecha_fin_parsed:
                pagos = pagos.filter(fecha_pago__range=[fecha_inicio_parsed, fecha_fin_parsed])
            else:
                messages.error(request, "La fecha de inicio debe ser anterior a la fecha final.")
        else:
            messages.error(request, "Formato de fecha inválido.")
    elif fecha_inicio or fecha_fin:
        messages.error(request, "Debe completar ambas fechas para aplicar el filtro.")

    if not fecha_inicio or not fecha_fin:
        paginator = Paginator(pagos, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        paginator = Paginator(pagos, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)


    total = sum(pago.valor for pago in page_obj)

    context = {
        "page_obj": page_obj,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "usuario_id": int(usuario_id) if usuario_id else None,
        "usuarios": User.objects.all(),  # <-- para el select
        "per_page_actual": int(request.GET.get('per_page', 15)),
        "cantidades_por_pagina": [
            200, 500, 1000, 2000, 5000, 10000, 20000, 50000
        ],
        "total": total
    }

    return render(request, 'estado.html', context)

















def error_403(request, exception):
    return render(request, '403.html', status=403)

def error_404(request, exception):
    return render(request, '404.html')



def error_500(request):
    return render(request, '500.html')
