def menu_items_context(request):
    user_permissions = set()
    if request.user.is_authenticated:
        user_permissions = request.user.get_all_permissions()

    menu_items = [
        {"name": "Lecturas", "icon": "fas fa-file-alt", "url": "lecturas", "permission": "control.view_lectura"},
        {"name": "Clientes", "icon": "fas fa-users", "url": "clientes", "permission": "control.view_cliente"},
        {"name": "Lugares", "icon": "fas fa-map-marker-alt", "url": "lugares", "permission": "control.view_lugar"},
        {"name": "Usuarios", "icon": "fas fa-user", "url": "usuarios", "permission": "auth.view_user"},
        {"name": "Grupos", "icon": "fas fa-user-friends", "url": "grupos", "permission": "auth.view_group"},
        {"name": "Estados de cuenta", "icon": "fas fa-chart-bar", "url": "estado", "permission": "control.view_pago"},
        {"name": "Solicitar cambio", "icon": "fas fa-comment-alt", "url": "crearSolicitud", "permission": "control.add_solicitud"},
        {"name": "Solicitudes", "icon": "fas fa-folder-open", "url": "solicitudes", "permission": "control.view_solicitud"},
        {"name": "Historial", "icon": "fas fa-history", "url": "historial", "permission": "auth.view_logentry"},
    ]

    filtered_menu_items = []
    if request.user.is_superuser:
        filtered_menu_items = menu_items
    else:
        for item in menu_items:
            if item['permission'] == "None" or item['permission'] in user_permissions:
                filtered_menu_items.append(item)

    return {
        "menu_items": filtered_menu_items
    }
