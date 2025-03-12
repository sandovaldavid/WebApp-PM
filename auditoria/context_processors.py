from .signals import set_current_user

def user_audit(request):
    """
    Context processor para establecer el usuario actual en cada request
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Establecer el usuario actual en el contexto global
        set_current_user(request.user)
        
        # Guardar ID del usuario en la sesión para uso posterior (e.g., durante logout)
        if hasattr(request, 'session'):
            request.session['last_user_id'] = request.user.pk
    return {}
