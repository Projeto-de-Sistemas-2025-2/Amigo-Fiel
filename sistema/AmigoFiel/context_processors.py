# AmigoFiel/context_processors.py
def perfis_flags(request):
    u = request.user
    return {
        "eh_empresa": hasattr(u, "perfil_empresa"),
        "eh_comum": hasattr(u, "perfil_comum"),
        "eh_ong": hasattr(u, "perfil_ong"),
    }
