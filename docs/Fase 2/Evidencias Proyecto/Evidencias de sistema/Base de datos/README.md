# Evidencia de sistema: base de datos

SEMAXEL usa MySQL 8 (utf8mb4). El esquema se genera con las migraciones de
Django que están en la carpeta `migrations/` de cada módulo (17 en total).

## Archivos

- `esquema_capstone_semaxel.sql`: estructura completa de la base de datos
  `capstone_semaxel`, exportada con `mysqldump --no-data` el 22/10/2026. Solo
  incluye tablas, claves y restricciones; no incluye datos ni contraseñas.

## Tablas

El esquema tiene 27 tablas:

- **18 del sistema**, documentadas en
  `Evidencias de documentación/03 ARQUITECTURA  Y DISEÑO TECNICO/Modelo_Base_Datos_MySQL_SEMAXEL_COMPLETADO.docx`:
  17 tablas propias (usuarios, empresas, sucursales, técnicos, tickets,
  ofertas, órdenes de trabajo, SLA, mantenimiento y sus tablas de unión) más
  `auth_user`.
- **9 internas de Django**: grupos y permisos (`auth_group`,
  `auth_group_permissions`, `auth_permission`, `auth_user_groups`,
  `auth_user_user_permissions`), sesiones (`django_session`), migraciones
  (`django_migrations`), tipos de contenido (`django_content_type`) y registro
  del panel de administración (`django_admin_log`).

## Cómo recrear la base

```bash
python manage.py migrate
```
