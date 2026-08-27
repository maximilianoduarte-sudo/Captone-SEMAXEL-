# Sistema de Gestión de Mantenimiento de Infraestructura

Aplicación web para la gestión del mantenimiento de la infraestructura física
de sucursales. Permite administrar sucursales, técnicos, especialidades,
tickets, ofertas de trabajo, órdenes de trabajo, SLA y mantenimiento
preventivo, e incluye un dashboard con indicadores.

Proyecto de título de Ingeniería en Informática.

## Stack tecnológico

- Python 3.10
- Django 5.2
- MySQL 8.0
- Django ORM
- HTML5 / CSS3
- Bootstrap 5
- JavaScript
- Chart.js
- Git / GitHub

## Estructura del proyecto

```text
Capstone-SEMAXEL/
├── config/            # Configuración del proyecto Django
├── accounts/          # Usuarios y roles
├── sucursales/        # Sucursales
├── tecnicos/          # Técnicos y especialidades
├── tickets/           # Tickets y órdenes de trabajo
├── ofertas/           # Ofertas de trabajo para técnicos
├── sla/               # SLA
├── mantenimiento/     # Mantenimiento preventivo
├── dashboard/         # Dashboard con indicadores
├── templates/         # Plantillas globales
├── static/            # CSS, JS, Bootstrap, Chart.js
├── media/             # Archivos subidos (imágenes, etc.)
├── manage.py
├── requirements.txt
├── .env               # Variables de entorno (no versionado)
└── .gitignore
```

## Requisitos previos

- Python 3.10 o superior instalado.
- MySQL 8.0 instalado y en ejecución (servicio `MySQL80`).
- Git instalado.

## Pasos para ejecutar el proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Captone-SEMAXEL-.git
cd Captone-SEMAXEL-
```

### 2. Crear el entorno virtual

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

En Windows (PowerShell):

```bash
venv\Scripts\activate
```

En Windows (CMD):

```bash
venv\Scripts\activate.bat
```

En Linux / macOS:

```bash
source venv/bin/activate
```

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar las variables de entorno

Copiar las variables necesarias al archivo `.env` (en la raíz del proyecto).
Este archivo NO se versiona en Git.

```text
# Configuración de la base de datos MySQL
DB_NAME=capstone_semaxel
DB_USER=root
DB_PASSWORD=TU_CONTRASEÑA
DB_HOST=localhost
DB_PORT=3306

# Configuración general de Django
SECRET_KEY=TU_SECRET_KEY
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> La `SECRET_KEY` puede generarse con:
> `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 6. Crear la base de datos MySQL

Con el cliente de MySQL, crear la base de datos si no existe:

```sql
CREATE DATABASE capstone_semaxel
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 7. Ejecutar las migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Crear un superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 9. Ejecutar el servidor

```bash
python manage.py runserver
```

Acceder a `http://127.0.0.1:8000/` desde el navegador. El panel de
administración está disponible en `http://127.0.0.1:8000/admin/`.

## Comando útiles

```bash
python manage.py check          # Verificar configuración
python manage.py runserver      # Levantar servidor de desarrollo
```

## Notas

- El archivo `.env` contiene credenciales y no debe subirse al repositorio.
- El entorno virtual `venv/` no se versiona en Git.
