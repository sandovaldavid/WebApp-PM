from dashboard.models import Notificacion


def notificaciones_usuario(request):
    """
    Context processor para proporcionar las notificaciones no leídas del usuario en todas las plantillas
    """
    context = {"notificaciones_no_leidas": 0, "user_notifications": []}

    if request.user.is_authenticated:
        # Obtener el número de notificaciones no leídas
        context["notificaciones_no_leidas"] = Notificacion.objects.filter(
            idusuario=request.user, leido=False, archivada=False
        ).count()

        # Obtener las notificaciones recientes no leídas para el dropdown
        context["user_notifications"] = Notificacion.objects.filter(
            idusuario=request.user, leido=False, archivada=False
        ).order_by("-fechacreacion")[
            :5
        ]  # Mostrar solo las 5 más recientes

    return context
