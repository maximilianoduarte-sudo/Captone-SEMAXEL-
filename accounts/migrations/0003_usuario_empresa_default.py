from django.db import migrations


def asignar_empresa_default(apps, schema_editor):
    """Asigna la empresa por defecto a los usuarios no-técnicos existentes."""
    Empresa = apps.get_model("empresas", "Empresa")
    Usuario = apps.get_model("accounts", "Usuario")

    empresa, _ = Empresa.objects.get_or_create(
        codigo="SEMAXEL",
        defaults={
            "nombre": "SEMAXEL",
            "rut": "76.128.123-4",
            "ciudad": "Santiago",
            "region": "Metropolitana",
        },
    )
    Usuario.objects.exclude(rol="TECNICO").filter(empresa__isnull=True).update(
        empresa=empresa
    )


def desasignar_empresa(apps, schema_editor):
    """Reverso: deja a todos los usuarios sin empresa."""
    Usuario = apps.get_model("accounts", "Usuario")
    Usuario.objects.update(empresa=None)


class Migration(migrations.Migration):

    dependencies = [
        ("empresas", "0001_initial"),
        ("accounts", "0002_usuario_empresa"),
    ]

    operations = [
        migrations.RunPython(asignar_empresa_default, desasignar_empresa),
    ]