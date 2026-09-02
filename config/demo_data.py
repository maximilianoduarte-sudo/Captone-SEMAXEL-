"""
Datos ficticios de demostración para el prototipo visual (Fase 3).

Estos datos solo sirven para visualizar la navegación y el diseño de la
interfaz. En fases posteriores se reemplazarán por consultas reales a la
base de datos. NO contienen credenciales reales.
"""

SUCURSALES = [
    {"id": 1, "nombre": "Providencia", "codigo": "PRO", "direccion": "Av. Providencia 1200", "ciudad": "Santiago", "region": "Metropolitana", "telefono": "+56 2 2345 1000", "correo": "providencia@semaxel.cl", "encargado": "Juan Pérez", "estado": "ACTIVA"},
    {"id": 2, "nombre": "Santiago Centro", "codigo": "STC", "direccion": "Huérfanos 789", "ciudad": "Santiago", "region": "Metropolitana", "telefono": "+56 2 2345 2000", "correo": "santiagocentro@semaxel.cl", "encargado": "María González", "estado": "ACTIVA"},
    {"id": 3, "nombre": "Ñuñoa", "codigo": "NUN", "direccion": "Av. Irarrázaval 3450", "ciudad": "Santiago", "region": "Metropolitana", "telefono": "+56 2 2345 3000", "correo": "nunoa@semaxel.cl", "encargado": "Carlos Díaz", "estado": "ACTIVA"},
    {"id": 4, "nombre": "Las Condes", "codigo": "LCO", "direccion": "Av. Apoquindo 4500", "ciudad": "Santiago", "region": "Metropolitana", "telefono": "+56 2 2345 4000", "correo": "lascondes@semaxel.cl", "encargado": "Ana Torres", "estado": "INACTIVA"},
]

ESPECIALIDADES = ["Electricidad", "Gasfitería", "Infraestructura", "Climatización", "Carpintería"]

CATEGORIAS = [
    {"id": 1, "nombre": "Fuga de agua", "especialidad": "Gasfitería"},
    {"id": 2, "nombre": "Fallo eléctrico", "especialidad": "Electricidad"},
    {"id": 3, "nombre": "Aire acondicionado", "especialidad": "Climatización"},
    {"id": 4, "nombre": "Infraestructura / Obra", "especialidad": "Infraestructura"},
    {"id": 5, "nombre": "Plomería", "especialidad": "Gasfitería"},
]

# Estados de tickets
ESTADOS = {
    "ABIERTO": "Abierto",
    "EN_REVISION": "En revisión",
    "PUBLICADO": "Publicado",
    "EN_EJECUCION": "En ejecución",
    "RESUELTO": "Resuelto",
    "CERRADO": "Cerrado",
    "CANCELADO": "Cancelado",
}

PRIORIDADES = {
    "BAJA": "Baja",
    "MEDIA": "Media",
    "ALTA": "Alta",
    "CRITICA": "Crítica",
}

TICKETS = [
    {"numero": "TK-00001", "titulo": "Fuga de agua en cocina", "sucursal": "Providencia", "categoria": "Fuga de agua", "prioridad": "ALTA", "estado": "ABIERTO", "fecha": "02/09/2026 08:15", "creador": "María González", "descripcion": "Se detectó una fuga de agua bajo el lavaplatos de la cocina principal. El piso se está mojando y requiere atención urgente para evitar daños mayores."},
    {"numero": "TK-00002", "titulo": "Fallo en iluminación de bodega", "sucursal": "Santiago Centro", "categoria": "Fallo eléctrico", "prioridad": "MEDIA", "estado": "EN_REVISION", "fecha": "02/09/2026 09:40", "creador": "Juan Pérez", "descripcion": "Las luminarias del sector bodega parpadean y dos no encienden. Posible sobrecarga en el circuito."},
    {"numero": "TK-00003", "titulo": "Aire acondicionado sin enfriar", "sucursal": "Ñuñoa", "categoria": "Aire acondicionado", "prioridad": "ALTA", "estado": "PUBLICADO", "fecha": "02/09/2026 10:05", "creador": "Carlos Díaz", "descripcion": "El equipo de aire acondicionado de la sala de reuniones no enfría correctamente. Temperatura ambiente superior a lo normal."},
    {"numero": "TK-00004", "titulo": "Drenaje obstruido en baño", "sucursal": "Providencia", "categoria": "Plomería", "prioridad": "MEDIA", "estado": "EN_EJECUCION", "fecha": "01/09/2026 15:30", "creador": "María González", "descripcion": "El lavaplatos del segundo baño tiene un drenaje lento por obstrucción. Se requiere despeje de cañerías."},
    {"numero": "TK-00005", "titulo": "Grifo con filtración", "sucursal": "Santiago Centro", "categoria": "Plomería", "prioridad": "BAJA", "estado": "RESUELTO", "fecha": "01/09/2026 11:20", "creador": "Juan Pérez", "descripcion": "El grifo del primer piso filtra permanente. Se reemplazó empaquetadura y quedó resuelto."},
    {"numero": "TK-00006", "titulo": "Pintura y reparación de muro", "sucursal": "Ñuñoa", "categoria": "Infraestructura / Obra", "prioridad": "BAJA", "estado": "CERRADO", "fecha": "31/08/2026 16:45", "creador": "Carlos Díaz", "descripcion": "Reparación de grietas y repintado de muro en el pasillo de acceso."},
]

HISTORIAL = {
    "TK-00001": [
        {"estado": "Abierto", "usuario": "María González", "fecha": "02/09/2026 08:15", "comentario": "Creación del ticket por incidencia."},
    ],
    "TK-00003": [
        {"estado": "Abierto", "usuario": "Carlos Díaz", "fecha": "02/09/2026 10:05", "comentario": "Creación del ticket por incidencia."},
        {"estado": "En revisión", "usuario": "Admin", "fecha": "02/09/2026 10:20", "comentario": "Revisión y clasificación de la incidencia."},
        {"estado": "Publicado", "usuario": "Admin", "fecha": "02/09/2026 10:30", "comentario": "Se publicó la oferta para técnicos."},
    ],
    "TK-00004": [
        {"estado": "Abierto", "usuario": "María González", "fecha": "01/09/2026 15:30", "comentario": "Creación del ticket por incidencia."},
        {"estado": "En revisión", "usuario": "Admin", "fecha": "01/09/2026 16:00", "comentario": "Clasificación de prioridad."},
        {"estado": "En ejecución", "usuario": "Técnico", "fecha": "02/09/2026 09:00", "comentario": "Trabajo en curso por técnico asignado."},
    ],
}

EVIDENCIAS = {
    "TK-00001": [
        {"nombre": "fuga_cocina_1.jpg", "tipo": "image"},
        {"nombre": "fuga_cocina_2.jpg", "tipo": "image"},
    ],
    "TK-00002": [
        {"nombre": "bodega_luz.jpg", "tipo": "image"},
    ],
}

OFERTAS = [
    {"id": 1, "ticket": "TK-00003", "titulo": "Aire acondicionado sin enfriar", "sucursal": "Ñuñoa", "direccion": "Av. Irarrázaval 3450", "categoria": "Aire acondicionado", "prioridad": "ALTA", "estado": "PUBLICADO", "publicacion": "hace 30 minutos", "vencimiento": "03/09/2026 18:00", "descripcion": "El equipo de aire acondicionado de la sala de reuniones no enfría correctamente. Revisar gas refrigerante y compresor."},
    {"id": 2, "ticket": "TK-00007", "titulo": "Reparación de tablero eléctrico", "sucursal": "Providencia", "direccion": "Av. Providencia 1200", "categoria": "Fallo eléctrico", "prioridad": "CRITICA", "estado": "PUBLICADO", "publicacion": "hace 1 hora", "vencimiento": "03/09/2026 12:00", "descripcion": "Cortocircuito en tablero general. Requiere técnica eléctrica certificada con urgencia."},
    {"id": 3, "ticket": "TK-00008", "titulo": "Mantención de sellos de ventanas", "sucursal": "Santiago Centro", "direccion": "Huérfanos 789", "categoria": "Infraestructura / Obra", "prioridad": "BAJA", "estado": "PUBLICADO", "publicacion": "hace 3 horas", "vencimiento": "05/09/2026 18:00", "descripcion": "Reemplazo de sellos de goma en ventanas del segundo piso para evitar filtraciones."},
    {"id": 4, "ticket": "TK-00009", "titulo": "Reparación de grifería", "sucursal": "Ñuñoa", "direccion": "Av. Irarrázaval 3450", "categoria": "Plomería", "prioridad": "MEDIA", "estado": "PUBLICADO", "publicacion": "hace 5 horas", "vencimiento": "04/09/2026 18:00", "descripcion": "Reparación de grifería del baño de personal con fuga en la base."},
]

# Estado de las órdenes de trabajo
ORDENES = [
    {"id": 1, "ticket": "TK-00004", "tecnico": "Juan Pérez", "sucursal": "Providencia", "estado": "EN_EJECUCION", "asignacion": "02/09/2026 09:00", "inicio": "02/09/2026 09:15", "fin": "—", "descripcion": "Despeje de cañerías y revisión de drenaje en baño. Se requiere inspección de trampa.", "observaciones": "El drenaje presenta acumulación de residuos. Se aplicará desatascador de forma manual."},
    {"id": 2, "ticket": "TK-00010", "tecnico": "María González", "sucursal": "Santiago Centro", "estado": "ASIGNADA", "asignacion": "02/09/2026 10:00", "inicio": "—", "fin": "—", "descripcion": "Reparación de luminaria LED en recepción.", "observaciones": "Pendiente de agenda para inicio de trabajo."},
    {"id": 3, "ticket": "TK-00005", "tecnico": "Carlos Díaz", "sucursal": "Santiago Centro", "estado": "RESUELTA", "asignacion": "01/09/2026 12:00", "inicio": "01/09/2026 12:30", "fin": "01/09/2026 13:45", "descripcion": "Reemplazo de empaquetadura de grifo en primer piso.", "observaciones": "Trabajo finalizado correctamente. Sin fugas posteriores."},
    {"id": 4, "ticket": "TK-00006", "tecnico": "Ana Torres", "sucursal": "Ñuñoa", "estado": "CERRADA", "asignacion": "31/08/2026 17:00", "inicio": "01/09/2026 09:00", "fin": "01/09/2026 16:00", "descripcion": "Reparación de grietas y repintado de muro de acceso.", "observaciones": "Orden cerrada con calificación 5.0."},
]

TECNICOS = [
    {"nombre": "Juan Pérez", "especialidades": ["Electricidad", "Gasfitería"], "estado": "DISPONIBLE", "completados": 23, "calificacion": 4.8, "sla": 95, "telefono": "+56 9 1234 5678"},
    {"nombre": "María González", "especialidades": ["Gasfitería", "Plomería"], "estado": "OCUPADO", "completados": 18, "calificacion": 4.9, "sla": 98, "telefono": "+56 9 2345 6789"},
    {"nombre": "Carlos Díaz", "especialidades": ["Climatización", "Electricidad"], "estado": "DISPONIBLE", "completados": 31, "calificacion": 4.6, "sla": 90, "telefono": "+56 9 3456 7890"},
    {"nombre": "Ana Torres", "especialidades": ["Infraestructura", "Carpintería"], "estado": "NO_DISPONIBLE", "completados": 12, "calificacion": 4.7, "sla": 92, "telefono": "+56 9 4567 8901"},
    {"nombre": "Luis Fernández", "especialidades": ["Electricidad"], "estado": "INACTIVO", "completados": 40, "calificacion": 4.5, "sla": 88, "telefono": "+56 9 5678 9012"},
]

PLANES_MANTENIMIENTO = [
    {"nombre": "Revisión de extintores", "frecuencia": "Mensual", "sucursal": "Providencia", "proxima": "05/09/2026", "estado": "PROGRAMADO"},
    {"nombre": "Limpieza de rejillas de aire", "frecuencia": "Trimestral", "sucursal": "Santiago Centro", "proxima": "12/09/2026", "estado": "PROGRAMADO"},
    {"nombre": "Mantención de generador", "frecuencia": "Semestral", "sucursal": "Ñuñoa", "proxima": "20/10/2026", "estado": "PROGRAMADO"},
    {"nombre": "Revisión tableros eléctricos", "frecuencia": "Anual", "sucursal": "Providencia", "proxima": "15/11/2026", "estado": "PROGRAMADO"},
    {"nombre": "Inspección de techo", "frecuencia": "Trimestral", "sucursal": "Las Condes", "proxima": "01/10/2026", "estado": "VENCIDO"},
    {"nombre": "Mantención de aire acondicionado", "frecuencia": "Semestral", "sucursal": "Ñuñoa", "proxima": "22/12/2026", "estado": "PROGRAMADO"},
]


def get_ticket(numero):
    for t in TICKETS:
        if t["numero"] == numero:
            return t
    return None


def get_oferta(oid):
    for o in OFERTAS:
        if o["id"] == int(oid):
            return o
    return None


def get_orden(oid):
    for o in ORDENES:
        if o["id"] == int(oid):
            return o
    return None


def get_tecnico(nombre):
    for t in TECNICOS:
        if t["nombre"] == nombre:
            return t
    return None
