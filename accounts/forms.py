from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from empresas.models import Empresa
from tecnicos.models import Especialidad

from .models import Usuario


class LoginForm(AuthenticationForm):
    """Formulario de acceso con estilos del sistema."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "usuario@semaxel.cl",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "••••••••",
        })


class _UsuarioBaseForm(forms.ModelForm):
    """Base para crear/editar usuarios: datos de auth.User + rol, teléfono y empresa."""

    rol = forms.ChoiceField(choices=Usuario.Rol.choices, label="Rol")
    telefono = forms.CharField(max_length=30, required=False, label="Teléfono")
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        required=False,
        label="Empresa",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
            "is_active": "Activo",
        }

    def __init__(self, *args, **kwargs):
        self._perfil = kwargs.pop("perfil", None)
        self._empresas = kwargs.pop("empresas", None)
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            else:
                campo.widget.attrs.setdefault("class", "form-control")
        if self._empresas is not None:
            self.fields["empresa"].queryset = self._empresas
        if self._perfil:
            self.fields["rol"].initial = self._perfil.rol
            self.fields["telefono"].initial = self._perfil.telefono
            self.fields["empresa"].initial = self._perfil.empresa

    def clean_empresa(self):
        """Los no-técnicos deben pertenecer a una empresa del alcance del editor."""
        rol = self.cleaned_data.get("rol")
        empresa = self.cleaned_data.get("empresa")
        if rol == Usuario.Rol.TECNICO:
            return None
        if empresa is None:
            raise forms.ValidationError(
                "Selecciona la empresa (o usa el rol Técnico, que no requiere empresa)."
            )
        return empresa

    def _guardar_perfil(self, user):
        empresa = self.cleaned_data["empresa"]
        if self._perfil is not None:
            self._perfil.rol = self.cleaned_data["rol"]
            self._perfil.telefono = self.cleaned_data.get("telefono") or None
            self._perfil.empresa = empresa
            self._perfil.user = user
            self._perfil.save()
        else:
            Usuario.objects.create(
                user=user,
                rol=self.cleaned_data["rol"],
                telefono=self.cleaned_data.get("telefono") or None,
                empresa=empresa,
            )


class UsuarioCrearForm(_UsuarioBaseForm):
    """Creación de usuario con contraseña (dos campos para confirmar)."""

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta(_UsuarioBaseForm.Meta):
        fields = [
            "username", "first_name", "last_name", "email",
            "rol", "telefono", "password", "password2",
        ]

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirmacion = cleaned.get("password2")
        if password and confirmacion and password != confirmacion:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self._guardar_perfil(user)
        return user


class UsuarioEditarForm(_UsuarioBaseForm):
    """Edición de usuario; la contraseña queda vacía si no se desea cambiar."""

    password = forms.CharField(
        label="Nueva contraseña (dejar en blanco para conservarla)",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta(_UsuarioBaseForm.Meta):
        fields = [
            "username", "first_name", "last_name", "email",
            "is_active", "rol", "telefono", "password",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self._guardar_perfil(user)
        return user


class MiPerfilForm(forms.ModelForm):
    """El usuario autenticado actualiza sus propios datos básicos y teléfono."""

    telefono = forms.CharField(max_length=30, required=False, label="Teléfono")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        perfil = getattr(self.instance, "perfil", None)
        if perfil:
            self.fields["telefono"].initial = perfil.telefono

    def save(self, commit=True):
        user = super().save(commit=commit)
        perfil, _ = Usuario.objects.get_or_create(user=user)
        perfil.telefono = self.cleaned_data.get("telefono") or None
        perfil.save()
        return user


class _RegistroBaseForm(forms.Form):
    """Datos comunes del registro público (usuario + contraseña confirmada)."""

    username = forms.CharField(max_length=150, label="Nombre de usuario")
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif not campo.widget.attrs.get("class"):
                campo.widget.attrs.setdefault("class", "form-control")
        for campo, etiqueta in self.fields.items():
            if etiqueta.help_text:
                etiqueta.widget.attrs["aria-describedby"] = f"help-{campo}"

    def _validar_password(self):
        cleaned = self.cleaned_data
        password = cleaned.get("password")
        confirmacion = cleaned.get("password2")
        if password and confirmacion and password != confirmacion:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password:
            try:
                validate_password(password, self.cleaned_data.get("username"))
            except forms.ValidationError as error:
                self.add_error("password", error)

    def _validar_username(self):
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username__iexact=username).exists():
            self.add_error("username", "Ese nombre de usuario ya está en uso.")

    def clean(self):
        cleaned = super().clean()
        self._validar_username()
        self._validar_password()
        return cleaned


class RegistroGestorForm(_RegistroBaseForm):
    """Registro de una Empresa junto a su usuario GESTOR."""

    empresa_nombre = forms.CharField(max_length=150, label="Nombre de la empresa")
    rut = forms.CharField(
        max_length=20,
        label="RUT",
        help_text="Identificador tributario único (ej. 77.123.456-5).",
    )
    codigo = forms.CharField(
        max_length=20,
        label="Código de empresa",
        help_text="Identificador corto, se usa en los números de ticket (ej. SEMAXEL).",
    )
    ciudad = forms.CharField(max_length=100, required=False, label="Ciudad")
    region = forms.CharField(max_length=100, required=False, label="Región")
    telefono_empresa = forms.CharField(
        max_length=30, required=False, label="Teléfono de la empresa"
    )
    correo_empresa = forms.EmailField(required=False, label="Correo de la empresa")

    def clean(self):
        cleaned = super().clean()
        rut = cleaned.get("rut")
        codigo = cleaned.get("codigo")
        if rut and Empresa.objects.filter(rut__iexact=rut).exists():
            self.add_error("rut", "Ya existe una empresa con ese RUT.")
        if codigo and Empresa.objects.filter(codigo__iexact=codigo).exists():
            self.add_error("codigo", "Ya existe una empresa con ese código.")
        return cleaned

    def save(self):
        cleaned = self.cleaned_data
        empresa = Empresa.objects.create(
            nombre=cleaned["empresa_nombre"],
            rut=cleaned["rut"],
            codigo=cleaned["codigo"],
            ciudad=cleaned.get("ciudad") or "",
            region=cleaned.get("region") or "",
            telefono=cleaned.get("telefono_empresa") or "",
            correo=cleaned.get("correo_empresa") or "",
        )
        user = User.objects.create_user(
            username=cleaned["username"],
            first_name=cleaned["first_name"],
            last_name=cleaned["last_name"],
            email=cleaned["email"],
            password=cleaned["password"],
        )
        Usuario.objects.create(user=user, rol=Usuario.Rol.GESTOR, empresa=empresa)
        return user


class RegistroTecnicoForm(_RegistroBaseForm):
    """Registro público de un Técnico de mantenimiento."""

    telefono = forms.CharField(max_length=30, required=False, label="Teléfono")
    especialidades = forms.ModelMultipleChoiceField(
        queryset=Especialidad.objects.filter(activo=True),
        required=False,
        label="Especialidades",
        widget=forms.SelectMultiple(
            attrs={"class": "form-select", "size": 5}
        ),
    )

    def save(self):
        cleaned = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned["username"],
            first_name=cleaned["first_name"],
            last_name=cleaned["last_name"],
            email=cleaned["email"],
            password=cleaned["password"],
        )
        Usuario.objects.create(
            user=user,
            rol=Usuario.Rol.TECNICO,
            empresa=None,
            telefono=cleaned.get("telefono") or None,
        )
        return user