from django.db import migrations, models

import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("empresas", "0001_initial"),
        ("sucursales", "0003_empresa_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sucursal",
            name="empresa",
            field=models.ForeignKey(
                help_text="Empresa a la que pertenece la sucursal.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sucursales",
                to="empresas.empresa",
                verbose_name="Empresa",
            ),
        ),
    ]