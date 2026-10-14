from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from tecnicos.models import Tecnico

from .forms import (
    LoginForm,
    MiPerfilForm,
    RegistroGestorForm,
    RegistroTecnicoForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
)
from .models import Usuario
from .roles import empresas_visibles, rol_requerido, rol_usuario


def _inicio_usuario(user):
    """URL de inicio según el rol (los técnicos entran directo a Ofertas)."""
    if rol_usuario(user) == Usuario.Rol.TECNICO:
        return reverse_lazy("ofertas:disponibles")
    return reverse_lazy("dashboard")


def _sincronizar_tecnico(user, rol):
    """Crea el perfil de Tecnico cuando el usuario tiene rol TECNICO."""
    if rol != Usuario.Rol.TECNICO:
        return
    telefono = getattr(getattr(user, "perfil", None), "telefono", "") or ""
    Tecnico.objects.get_or_create(
        usuario=user,
        defaults={
            "telefono": telefono,
            "documento": f"DOC-{user.username.upper()}",
            "estado": Tecnico.Estado.DISPONIBLE,
        },
    )


class LoginView(DjangoLoginView):
    """Acceso con la autenticación estándar de Django."""

    template_name = "dashboard/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        """Tras el login, el técnico va a Ofertas (su espacio de trabajo)."""
        if rol_usuario(self.request.user) == Usuario.Rol.TECNICO:
            return reverse("ofertas:disponibles")
        return reverse("dashboard")

    def get_success_url(self):
        url = self.get_redirect_url()
        if url:
            return url
        return self.get_default_redirect_url()


login = LoginView.as_view()


def logout(request):
    """Cierra la sesión del usuario (GET o POST) y vuelve al login."""
    auth_logout(request)
    return redirect("login")


@login_required
def perfil(request):
    """Perfil del usuario autenticado; permite editar sus datos básicos."""
    form = MiPerfilForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("perfil")
    return render(request, "dashboard/perfil.html", {"form": form})


def _usuarios_visibles(user):
    """Usuarios según el rol: superuser ve todos; el resto, los de su empresa.

    Los usuarios sin empresa (los técnicos del marketplace) quedan fuera: su
    administración es del superusuario, no de un ADMIN de empresa.
    """
    qs = User.objects.select_related("perfil").order_by("username")
    if user.is_superuser:
        return qs
    return qs.filter(perfil__empresa__in=empresas_visibles(user))


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def usuarios(request):
    """Listado paginado de usuarios del sistema (alcance por empresa).

    Restringido a ADMIN: el GESTOR no administra usuarios globalmente.
    """
    qs = _usuarios_visibles(request.user)
    paginator = Paginator(qs, 10)
    usuarios = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/lista.html", {"usuarios": usuarios})


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def usuario_nuevo(request):
    """Crea un usuario y su perfil (rol, teléfono, empresa)."""
    form = UsuarioCrearForm(
        request.POST or None,
        empresas=empresas_visibles(request.user),
    )
    if form.is_valid():
        user = form.save()
        _sincronizar_tecnico(user, form.cleaned_data["rol"])
        messages.success(request, f"Usuario {user.username} creado correctamente.")
        return redirect("usuarios")
    return render(request, "accounts/form.html", {"form": form, "titulo": "Nuevo usuario"})


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def usuario_editar(request, pk):
    """Edita un usuario existente, su rol y (opcionalmente) su contraseña."""
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser:
        perfil_existente = getattr(user, "perfil", None)
        visibles = empresas_visibles(request.user)
        # Un ADMIN solo administra usuarios de su empresa. Los técnicos no
        # pertenecen a ninguna (son un recurso global del marketplace), así que
        # editar sus cuentas queda reservado al superusuario: de lo contrario
        # un ADMIN podría resetear su contraseña y cambiarle el rol.
        permite = (
            perfil_existente is None
            or (
                perfil_existente.empresa_id is not None
                and visibles.filter(pk=perfil_existente.empresa_id).exists()
            )
        )
        if not permite:
            raise PermissionDenied
    perfil, _ = Usuario.objects.get_or_create(user=user)
    form = UsuarioEditarForm(
        request.POST or None,
        instance=user,
        perfil=perfil,
        empresas=empresas_visibles(request.user),
    )
    if form.is_valid():
        form.save()
        _sincronizar_tecnico(user, form.cleaned_data["rol"])
        messages.success(request, f"Usuario {user.username} actualizado correctamente.")
        return redirect("usuarios")
    return render(request, "accounts/form.html", {
        "form": form,
        "titulo": f"Editar usuario {user.username}",
    })


def registro(request):
    """Página pública para elegir el tipo de registro (GESTOR o TÉCNICO)."""
    if request.user.is_authenticated:
        return redirect(_inicio_usuario(request.user))
    return render(request, "accounts/registro.html")


def registro_gestor(request):
    """Registro público de una Empresa con su usuario GESTOR.

    Crea la Empresa (ACTIVA) y el usuario con rol GESTOR asociado a ella.
    No se permite elegir rol: el rol GESTOR es fijo del flujo.
    """
    if request.user.is_authenticated:
        return redirect(_inicio_usuario(request.user))
    form = RegistroGestorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            "Empresa y usuario GESTOR creados correctamente. Ya puedes iniciar sesión.",
        )
        return redirect("login")
    return render(request, "accounts/registro_gestor.html", {"form": form})


def registro_tecnico(request):
    """Registro público de un TÉCNICO de servicio de mantenimiento.

    Crea el usuario con rol TECNICO y su perfil de técnico (vía
    _sincronizar_tecnico), incluyendo especialidades seleccionadas.
    El técnico no queda asociado a ninguna empresa administrada.
    """
    if request.user.is_authenticated:
        return redirect(_inicio_usuario(request.user))
    form = RegistroTecnicoForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        _sincronizar_tecnico(user, Usuario.Rol.TECNICO)
        especialidades = form.cleaned_data.get("especialidades")
        if especialidades and hasattr(user, "tecnico"):
            user.tecnico.especialidades.set(especialidades)
        messages.success(
            request,
            "Tu perfil de técnico se creó correctamente. Ya puedes iniciar sesión.",
        )
        return redirect("login")
    return render(request, "accounts/registro_tecnico.html", {"form": form})