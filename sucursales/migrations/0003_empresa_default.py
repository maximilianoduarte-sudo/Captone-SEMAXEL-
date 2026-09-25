from django.db import migrations


def crear_empresa_default(apps, schema_editor):
    """Crea la empresa por defecto y asigna todas las sucursales existentes."""
    Empresa = apps.get_model("empresas", "Empresa")
    Sucursal = apps.get_model("sucursales", "Sucursal")

    empresa, _ = Empresa.objects.get_or_create(
        codigo="SEMAXEL",
        defaults={
            "nombre": "SEMAXEL",
            "rut": "76.128.123-4",
            "ciudad": "Santiago",
            "region": "Metropolitana",
        },
    )
    Sucursal.objects.filter(empresa__isnull=True).update(empresa=empresa)


def desasignar_empresa(apps, schema_editor):
    """Reverso: deja las sucursales sin empresa (aplica antes de 0004)."""
    Sucursal = apps.get_model("sucursales", "Sucursal")
    Sucursal.objects.update(empresa=None)


class Migration(migrations.Migration):

    dependencies = [
        ("empresas", "0001_initial"),
        ("sucursales", "0002_sucursal_empresa_alter_sucursal_codigo_and_more"),
    ]

    operations = [
        migrations.RunPython(crear_empresa_default, desasignar_empresa),
    ]