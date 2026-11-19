# Guía de pruebas manuales (entorno de QA)

Cómo probar a mano **toda** la app del técnico y la web con datos falsos
propios, sin mezclarlos con los de demostración. Creada el 15-11-2026 y
ampliada el mismo día para cubrir el sistema completo. Complementa la
[Bitácora](Bitacora_App_Movil.md) (partes 9.2 y 9.3), la
[Guía del entorno](Guia_Entorno_Desarrollo.md) (emulador, sección 3.6) y la
[Guía del servidor de pruebas](Guia_Servidor_Pruebas.md).

> **Todos los datos de QA son falsos (hipotéticos).** La columna "Resultado"
> de los casos de prueba se deja en blanco para que la llene quien prueba; no
> se completa sin haber hecho la prueba.

---

## 1. Qué crea `preparar_qa`

### 1.1 Empresas y sucursales

| Empresa | Para qué |
|---|---|
| **QA Retail SpA** (código `QA`) | La empresa que se prueba. |
| **QA Otra Empresa** (código `QAOTRA`) | Comprobar que una empresa no ve los datos de otra. |

| Sucursal (código) | GPS | Horario | Encargado | Para qué |
|---|---|---|---|---|
| QA Providencia (`QPR`) | Sí | L-V 9-20, S 9-14 | `qa_encargado` | Llegada dentro del radio |
| QA Ñuñoa (`QNU`) | Sí | L-S 10-19 | `qa_encargado` | Llegada fuera del radio |
| QA Santiago Centro (`QSC`) | Sí | Todos los días 8-22 | — | Sucursal fuera del alcance del encargado |
| QA Maipú (`QMA`) | **No** | **Sin horario** | — | Llegada "no verificable" y "Horario no informado" |
| QA Las Condes (`QLC`) | Sí | L-V 9-20, S 9-14 | — | Sucursal **inactiva** |
| QA Otra Sucursal (`QOT`) | Sí | L-V 9-20, S 9-14 | — | Es de la otra empresa |

### 1.2 Usuarios (uno por rol)

Todos tienen **la misma contraseña**, aleatoria, que **no está en el
repositorio** (que es público). En este equipo está guardada en
`D:\herramientas-servidor\credenciales\qa.txt`.

| Usuario | Rol | Dónde entra | Qué tiene de especial |
|---|---|---|---|
| `qa_admin` | Administrador (QA) | Web | Ve todo lo de QA Retail |
| `qa_gestor` | Gestor (QA) | Web | Gestiona tickets y ofertas |
| `qa_encargado` | Encargado (QA) | Web | Solo ve QA Providencia y QA Ñuñoa |
| `qa_gerencia` | Gerencia (QA) | Web | Solo lectura: no puede cambiar estados |
| `qa_tecnico` | Técnico | App | Electricidad, Gasfitería, Infraestructura. Tiene órdenes en todos los estados |
| `qa_tecnico2` | Técnico | App | Climatización y Carpintería. Tiene una orden en ejecución |
| `qa_tecnico_nodisp` | Técnico | App | Estado **No disponible** |
| `qa_tecnico_inactivo` | Técnico | App | Estado **Inactivo**: no puede entrar a la app |
| `qa_otra_admin` | Administrador (QA Otra) | Web | Solo ve QA Otra Empresa |

Además, `qa_tecnico` tiene un celular registrado (falso) para las
notificaciones push.

### 1.3 Tickets

Se crean con las mismas reglas de la web y la app (tomar, llegar, iniciar,
fotos, firma, resolver, cerrar), así que el historial, los estados y la
disponibilidad de los técnicos son coherentes. Los trabajos terminados quedan
repartidos en las últimas semanas para que los reportes tengan historia.

| Ticket | Estado | Sucursal | Qué se prueba |
|---|---|---|---|
| QA-00001 | Publicado (oferta 3 días) | QPR | App: flujo completo con llegada **dentro** del radio |
| QA-00002 | Publicado (oferta 2 días) | QNU | App: llegada **fuera** del radio |
| QA-00003 | Publicado (oferta **2 horas**), crítica | QSC | App: oferta urgente |
| QA-00004 | Publicado, Climatización | QPR | App: `qa_tecnico` **no** la ve; `qa_tecnico2` sí |
| QA-00005 | En ejecución, orden **asignada** a `qa_tecnico` | QSC | App: llegada, iniciar, fotos y firma |
| QA-00006 | Oferta **vencida** | QNU | App: no aparece. Web: vuelve a revisión al expirar |
| QA-00007 | Publicado | QMA | App: sucursal sin GPS ni horario |
| QA-00008 | Orden **en ejecución** (2 fotos, sin firma) | QPR | App: firma y resolver |
| QA-00009 | Orden **resuelta** (fotos y firma) | QNU | Web: cerrar con calificación o reabrir |
| QA-00010 | **Cerrado** hace 20 días, nota 5, dentro del SLA | QPR | Reportes |
| QA-00011 | **Cerrado** hace 12 días, nota 3, **fuera del SLA**, llegada fuera del radio | QSC | Reportes y SLA |
| QA-00012 | **Cancelado** hace 5 días | QNU | Estado terminal |
| QA-00013 | Orden en ejecución de `qa_tecnico2` | QSC | App: `qa_tecnico` no la ve ni puede tocarla |
| QA-00014 | **Abierto** hace 2 días, crítica, con foto adjunta y **SLA vencido** | QPR | Web: revisar y publicar |
| QA-00015 | **En revisión** | QNU | Web: publicar la oferta |
| QA-00016 | Cerrado hace 25 días por `qa_tecnico2`, nota 4 | QSC | Reportes: ranking de técnicos |
| QA-00017 | Cerrado hace 8 días, nota 4 | QNU | Reportes |
| QA-00018 | **Preventivo** abierto (generado por un plan) | QSC | Mantenimiento |
| QAOTRA-00001 | Abierto | QOT | Web: `qa_admin` **no** lo ve |
| QAOTRA-00002 | Publicado | QOT | App: los técnicos ven ofertas de cualquier empresa |

### 1.4 Planes de mantenimiento

| Plan | Sucursal | Frecuencia | Estado |
|---|---|---|---|
| Revisión mensual de tablero eléctrico | QPR | Mensual | **Vencido**: para probar el botón "Generar" |
| Mantención trimestral de aire acondicionado | QSC | Trimestral | Próximo en 20 días |
| Limpieza semanal de desagües | QNU | Semanal | **Pausado** (inactivo) |
| Inspección semestral de muros | QSC | Semestral | Ya generó el ticket QA-00018 |

---

## 2. Preparar y reiniciar

Con MySQL y el servidor encendidos (ver la Guía del servidor):

```powershell
cd D:\proyecto_semaxel
.\venv\Scripts\python.exe manage.py preparar_qa --archivo-clave D:\herramientas-servidor\credenciales\qa.txt
```

- **Cada ejecución deja todo como nuevo:** borra los tickets de las empresas
  de QA (con sus fotos, firmas y adjuntos, también los archivos) y los planes
  de QA, y los vuelve a crear. No toca los datos de `seed_demo`.
- **La contraseña no cambia** al volver a ejecutarlo, salvo que se agreguen
  usuarios nuevos o se use `--nueva-clave`. Sin `--archivo-clave`, la
  contraseña nueva se muestra una sola vez en la consola.
- **No envía notificaciones push** mientras prepara los datos.
- Requiere haber ejecutado `seed_demo` antes; si no, el comando lo avisa.

**Se acabaron los trabajos para probar.** Cuando las pruebas ya avanzaron
todas las órdenes activas de `qa_tecnico`, se puede sumar un lote nuevo **sin
borrar nada** (ni lo ya probado ni la contraseña):

```powershell
.\scripts\preparar-datos.ps1 -AgregarTrabajos
# o: .\venv\Scripts\python.exe manage.py preparar_qa --agregar-trabajos
```

Cada vez agrega 8 tickets con números nuevos (desde `QA-00019`): 3 órdenes
asignadas (en QA Providencia, QA Ñuñoa y QA Maipú sin GPS), 2 en ejecución con
2 fotos cada una y 3 ofertas para tomar. Se puede repetir las veces que haga
falta. En la app, tocar **Actualizar** en Inicio para verlos.

---

## 3. Coordenadas para probar el GPS

En el emulador: botón **⋯** (Extended controls) → **Location** → escribir
latitud y longitud → **Set location**. El radio permitido es de 150 m.

| Para probar | Latitud | Longitud | Resultado esperado |
|---|---|---|---|
| QA-00001, dentro del radio (QA Providencia) | -33.4295 | -70.6177 | Llegada verificada, a 0 m |
| QA-00001, cerca pero dentro (≈45 m) | -33.4299 | -70.6177 | Llegada verificada, a ≈45 m |
| QA-00002, fuera del radio (≈7 km de QA Ñuñoa) | -33.4489 | -70.6693 | Llegada registrada **fuera del radio**, con la distancia |
| QA-00005, dentro del radio (QA Santiago Centro) | -33.4394 | -70.6508 | Llegada verificada |
| QA-00007 (QA Maipú, sin GPS) | cualquiera | cualquiera | Llegada "no verificable" |

La llegada se registra **una sola vez** por orden. Para repetirla, reiniciar
el entorno (sección 2).

---

## 4. Casos de prueba de la app

Marcar el resultado con ✅ (como se esperaba) o ❌ (anotar qué pasó).

### 4.1 Inicio de sesión y perfil

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| A-01 | Entrar con una contraseña incorrecta | Mensaje de error; no entra | |
| A-02 | Entrar con `qa_tecnico` | Inicio: "Hola, QA Técnico", 2 trabajos activos | |
| A-03 | Entrar con `qa_admin` | No entra: la app es solo para técnicos | |
| A-04 | Entrar con `qa_tecnico_inactivo` | No entra: técnico inactivo | |
| A-05 | Entrar con `qa_tecnico_nodisp` | Entra; Perfil muestra "No disponible" | |
| A-06 | `qa_tecnico_nodisp`: cambiar a "Disponible" en Perfil | Cambia y queda guardado | |
| A-07 | `qa_tecnico`: cambiar disponibilidad estando ocupado | La app no lo permite | |

### 4.2 Ofertas

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| A-08 | `qa_tecnico`: abrir Ofertas | Aparecen QA-00001, 00002, 00003, 00007 y la de QA Otra Empresa; **no** QA-00004 ni QA-00006 | |
| A-09 | Abrir el detalle de QA-00003 | Crítica, sucursal, dirección, horario y vencimiento | |
| A-10 | Abrir el detalle de QA-00007 | "Horario no informado" | |
| A-11 | `qa_tecnico2`: abrir Ofertas | Aparece QA-00004 | |
| A-12 | `qa_tecnico`: tomar QA-00001 | Pasa a Trabajos como "Asignada"; desaparece de Ofertas | |

### 4.3 Trabajo en terreno

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| A-13 | QA-00001: ubicación de QA Providencia y registrar llegada | "Llegada verificada" con la distancia | |
| A-14 | QA-00001: iniciar sin diagnóstico | Pide el diagnóstico | |
| A-15 | QA-00001: iniciar con diagnóstico | Orden "En ejecución" | |
| A-16 | Sacar una foto con la cámara | La foto aparece en la orden | |
| A-17 | Elegir una foto de la galería | La foto aparece en la orden | |
| A-18 | Borrar una foto propia | Desaparece de la orden | |
| A-19 | QA-00008: dibujar la firma y guardarla | Queda registrada; no permite una segunda | |
| A-20 | QA-00008: resolver sin "trabajo realizado" | Pide el trabajo realizado | |
| A-21 | QA-00008: resolver con "trabajo realizado" | Orden "Resuelta" | |
| A-22 | QA-00002: tomar, poner la ubicación lejana y registrar llegada | "Fuera del radio", con la distancia en metros | |
| A-23 | QA-00007: tomar y registrar llegada | "No verificable" (la sucursal no tiene GPS) | |
| A-24 | QA-00005: llegada, iniciar, fotos y firma | Funciona igual que QA-00001 | |
| A-25 | Trabajos → "Todos" | Se ven también las resueltas, cerradas y canceladas | |
| A-26 | Abrir una orden cerrada (QA-00010) | Solo lectura: no permite fotos ni cambios | |

### 4.4 Errores

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| A-27 | Apagar el servidor y tocar "Actualizar" | Mensaje de error de conexión; la app no se cierra | |
| A-28 | Cerrar sesión | Vuelve al login; al reabrir la app pide entrar de nuevo | |

---

## 5. Casos de prueba de la web

### 5.1 Administrador (`qa_admin`)

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| W-01 | Dashboard | Indicadores y gráficos con datos de QA (todos los estados) | |
| W-02 | Reportes | Cumplimiento de SLA menor a 100 % (por QA-00011), calificación promedio 4, ranking con `qa_tecnico` y `qa_tecnico2` | |
| W-03 | Tickets | Se ven los QA-; **no** aparece ningún QAOTRA- | |
| W-04 | Abrir QA-00014 | Foto adjunta visible; SLA vencido | |
| W-05 | QA-00014: pasar a revisión y publicar la oferta | Queda publicado; la oferta aparece en la app | |
| W-06 | Crear un ticket nuevo en QA Providencia | Número `QA-000NN` siguiente | |
| W-07 | Órdenes → QA-00009: cerrar sin calificación | Pide la calificación | |
| W-08 | Órdenes → QA-00009: cerrar con calificación | Ticket "Cerrado"; la nota suma en reportes | |
| W-09 | Abrir la orden de QA-00011 | Tarjeta "Registro en terreno": llegada fuera del radio, fotos y firma | |
| W-10 | Sucursales | Se ven las 5 de QA (una inactiva, una sin GPS) | |
| W-11 | Editar QA Maipú y agregarle latitud y longitud | Se guarda | |
| W-12 | Técnicos | Se ven los 4 técnicos de QA con sus estados | |
| W-13 | Mantenimiento → "Generar" | Crea un preventivo del plan vencido de QA Providencia | |
| W-14 | Usuarios: crear un usuario nuevo | Se crea con el rol elegido | |
| W-15 | Empresas | Solo QA Retail | |

### 5.2 Otros roles

| # | Usuario | Pasos | Resultado esperado | Resultado |
|---|---|---|---|---|
| W-16 | `qa_encargado` | Tickets | Solo ve los de QA Providencia y QA Ñuñoa | |
| W-17 | `qa_encargado` | Abrir Reportes | Acceso denegado (403) | |
| W-18 | `qa_encargado` | QA-00015: publicar la oferta | Queda publicado | |
| W-19 | `qa_gerencia` | Dashboard y Reportes | Se ven | |
| W-20 | `qa_gerencia` | Intentar cambiar el estado de una orden | No tiene la opción: solo lectura | |
| W-21 | `qa_gestor` | Tickets y ofertas de QA | Se ven y puede gestionarlos | |
| W-22 | `qa_otra_admin` | Tickets | Solo QAOTRA-00001 y QAOTRA-00002 | |
| W-23 | `qa_tecnico` | Entrar a la web | No ve el Dashboard; su espacio es Ofertas | |
| W-24 | `qa_tecnico` | Órdenes de Trabajo → abrir una orden activa | Sin formulario de transición; aviso "se avanza desde la app SEMAXEL Técnico" | |
| W-25 | `qa_tecnico` | En esa orden, tarjeta "Contacto con la sucursal" | Botones WhatsApp (abre `wa.me` con el mensaje), Llamar y correo; nombre del encargado | |
| W-26 | `qa_tecnico` | Tomar una oferta desde la web | Se crea la orden (luego se avanza en la app) | |

---

## 6. Si algo falla

Anotar en la columna "Resultado" qué pasó y, si se puede, guardar una captura
(en el emulador, botón de cámara de la barra lateral) en
[`capturas/`](capturas/). Cada falla confirmada se agrega como hallazgo en la
bitácora.
