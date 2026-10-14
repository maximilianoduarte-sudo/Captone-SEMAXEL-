from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.http import unquote

from accounts.roles import ROLES_ENCARGADOS
from empresas.models import Empresa

from .models import Sucursal


class SucursalAdminForm(forms.ModelForm):
    """Formulario del admin que impide asignar encargados de otra empresa."""

    class Meta:
        model = Sucursal
        fields = "__all__"

    def clean_encargados(self):
        """Los encargados deben ser usuarios de la misma empresa que la sucursal."""
        encargados = self.cleaned_data.get("encargados")
        if not encargados:
            return encargados
        empresa = Empresa.objects.filter(pk=self.data.get("empresa")).first()
        if empresa is None:
            return encargados
        invalidos = encargados.exclude(
            perfil__empresa=empresa,
            perfil__rol__in=ROLES_ENCARGADOS,
        )
        if invalidos.exists():
            raise forms.ValidationError(
                "Solo pueden ser encargados usuarios de esta empresa."
            )
        return encargados


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    form = SucursalAdminForm
    list_display = ("nombre", "empresa", "codigo", "ciudad", "telefono", "estado")
    list_filter = ("empresa", "estado", "ciudad")
    search_fields = ("nombre", "codigo", "ciudad", "empresa__nombre")
    filter_horizontal = ("encargados",)

    def _empresa_de_sucursal(self, request):
        """Empresa de la sucursal en edición o de la empresa elegida al crear."""
        if request.resolver_match is not None:
            object_id = request.resolver_match.kwargs.get("object_id")
            if object_id:
                obj = self.get_object(request, unquote(object_id))
                if obj is not None:
                    return obj.empresa
        empresa_id = request.POST.get("empresa") or request.GET.get("empresa")
        if empresa_id:
            return Empresa.objects.filter(pk=empresa_id).first()
        return None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Acota los encargados a los usuarios de la empresa de la sucursal."""
        if db_field.name == "encargados":
            empresa = self._empresa_de_sucursal(request)
            if empresa is not None:
                kwargs["queryset"] = (
                    User.objects.filter(
                        perfil__empresa=empresa,
                        perfil__rol__in=ROLES_ENCARGADOS,
                    )
                    .select_related("perfil")
                    .order_by("username")
                )
        return super().formfield_for_manytomany(db_field, request, **kwargs)
