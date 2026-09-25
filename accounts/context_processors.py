def usuario_context(request):
    """Expone rol, empresa y estado de superusuario a todas las plantillas."""
    perfil = getattr(request.user, "perfil", None)
    return {
        "rol": perfil.rol if perfil else "",
        "empresa": perfil.empresa if perfil else None,
        "es_superuser": bool(request.user.is_superuser),
    }