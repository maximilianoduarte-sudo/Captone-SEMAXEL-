# Guía de pruebas manuales (perfil de QA)

Cómo probar a mano la app del técnico y la web con un **perfil de QA propio**,
sin mezclarlo con los datos de demostración. Creada el 15-11-2026. Complementa
la [Bitácora](Bitacora_App_Movil.md) (parte 9.2), la
[Guía del entorno](Guia_Entorno_Desarrollo.md) (emulador, sección 3.6) y la
[Guía del servidor de pruebas](Guia_Servidor_Pruebas.md).

> Todos los datos de QA son **hipotéticos**. La columna "Resultado" de los
> casos de prueba se deja en blanco para que la llene quien prueba; no se
> completa sin haber hecho la prueba.

---

## 1. Qué es el perfil de QA

El comando `python manage.py preparar_qa` crea dos usuarios y seis tickets de
prueba:

| Usuario | Rol | Para qué |
|---|---|---|
| `qa_tecnico` | Técnico | Probar la app móvil. Especialidades: Electricidad, Gasfitería e Infraestructura. A propósito **no** tiene Climatización. |
| `qa_admin` | Administrador (empresa SEMAXEL) | Revisar en la web los tickets y órdenes de QA: fotos, firma y registro de llegada. |

**Contraseña.** Es aleatoria y la misma para los dos usuarios. **No está en el
repositorio**, que es público: en este equipo está guardada en
`D:\herramientas-servidor\credenciales\qa.txt`.

**Tickets de prueba** (todos parten publicados, con su oferta):

| Ticket | Sucursal | Categoría | Prioridad | Oferta | Qué se prueba |
|---|---|---|---|---|---|
| QA-0001 | Providencia | Fallo eléctrico | Alta | Vence en 3 días | Flujo completo, con llegada **dentro** del radio |
| QA-0002 | Ñuñoa | Fuga de agua | Media | Vence en 2 días | Llegada **fuera** del radio |
| QA-0003 | Santiago Centro | Infraestructura / Obra | Crítica | Vence en 2 horas | Oferta urgente |
| QA-0004 | Providencia | Aire acondicionado | Alta | Vence en 2 días | **No** debe aparecer en la app (falta la especialidad) |
| QA-0005 | Santiago Centro | Plomería | Media | Ya tomada por `qa_tecnico` | Probar directo llegada, fotos y firma |
| QA-0006 | Ñuñoa | Fallo eléctrico | Baja | Venció hace 1 hora | **No** debe aparecer en la app (vencida) |

`qa_tecnico` también ve las ofertas de los datos de demostración que
corresponden a sus especialidades (por ejemplo, "Reparación de grifería" y
"Mantención de sellos de ventanas"). Es correcto.

---

## 2. Preparar y reiniciar

Con MySQL y el servidor encendidos (ver la Guía del servidor):

```powershell
cd D:\proyecto_semaxel
.\venv\Scripts\python.exe manage.py preparar_qa --archivo-clave D:\herramientas-servidor\credenciales\qa.txt
```

- **Cada ejecución deja el escenario como nuevo:** borra los tickets `QA-`
  (con sus órdenes, fotos y firmas, también los archivos) y los vuelve a crear.
  No toca los datos de `seed_demo`.
- **La contraseña no cambia** al volver a ejecutarlo. Para generar otra:
  agregar `--nueva-clave`. Sin `--archivo-clave`, la contraseña nueva se
  muestra una sola vez en la consola.
- Requiere haber ejecutado `seed_demo` antes; si no, el comando lo avisa.

---

## 3. Coordenadas para probar el GPS

En el emulador: botón **⋯** (Extended controls) → **Location** → escribir
latitud y longitud → **Set location**. El radio permitido es de 150 m
(`SEMAXEL_RADIO_LLEGADA_METROS`).

| Para probar | Latitud | Longitud | Resultado esperado |
|---|---|---|---|
| QA-0001, dentro del radio (Providencia) | -33.4295 | -70.6177 | Llegada verificada, a 0 m |
| QA-0001, cerca pero dentro (≈45 m) | -33.4299 | -70.6177 | Llegada verificada, a ≈45 m |
| QA-0002, fuera del radio (≈7 km de Ñuñoa) | -33.4489 | -70.6693 | Llegada registrada **fuera del radio**, con la distancia |
| QA-0005, dentro del radio (Santiago Centro) | -33.4394 | -70.6508 | Llegada verificada |

La llegada se registra **una sola vez** por orden. Para repetirla, reiniciar
el escenario (sección 2).

---

## 4. Casos de prueba

Entrar a la app con `qa_tecnico`. Marcar el resultado con ✅ (como se
esperaba) o ❌ (anotar qué pasó).

### 4.1 Inicio de sesión y perfil

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| QA-01 | Entrar con una contraseña incorrecta | Mensaje de error; no entra | |
| QA-02 | Entrar con `qa_tecnico` y la contraseña correcta | Pantalla Inicio: "Hola, QA Técnico", 1 trabajo activo | |
| QA-03 | Entrar con `qa_admin` en la app | No entra: la app es solo para técnicos | |
| QA-04 | Perfil: ver datos y especialidades | Electricidad, Gasfitería e Infraestructura | |
| QA-05 | Perfil: cambiar disponibilidad estando ocupado | La app no lo permite (tiene un trabajo activo) | |

### 4.2 Ofertas

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| QA-06 | Abrir Ofertas | Aparecen QA-0001, QA-0002 y QA-0003 (más las de demo); **no** QA-0004 ni QA-0006 | |
| QA-07 | Abrir el detalle de QA-0003 | Muestra prioridad crítica, sucursal, dirección, horario y vencimiento | |
| QA-08 | Tomar QA-0001 | Pasa a Trabajos como "Asignada"; desaparece de Ofertas | |

### 4.3 Trabajo en terreno (QA-0001)

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| QA-09 | Fijar la ubicación de Providencia y registrar llegada | "Llegada verificada" con la distancia | |
| QA-10 | Iniciar el trabajo sin diagnóstico | Pide el diagnóstico | |
| QA-11 | Iniciar con diagnóstico | Orden "En ejecución" | |
| QA-12 | Evidencias: sacar una foto con la cámara | La foto aparece en la orden | |
| QA-13 | Evidencias: elegir una foto de la galería | La foto aparece en la orden | |
| QA-14 | Borrar una foto propia | Desaparece de la orden | |
| QA-15 | Firma: dibujar y guardar con el nombre del encargado | La firma queda registrada; no permite una segunda | |
| QA-16 | Resolver sin "trabajo realizado" | Pide el trabajo realizado | |
| QA-17 | Resolver con "trabajo realizado" | Orden "Resuelta" | |

### 4.4 Otros casos

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| QA-18 | QA-0002: tomar, poner la ubicación lejana y registrar llegada | Queda registrada "fuera del radio", con la distancia en metros | |
| QA-19 | QA-0005: registrar llegada, fotos y firma sin tomar nada | Funciona igual que QA-0001 | |
| QA-20 | Apagar el servidor y tocar "Actualizar" | Mensaje de error de conexión; la app no se cierra | |
| QA-21 | Cerrar sesión | Vuelve al login; al reabrir la app pide entrar de nuevo | |

### 4.5 Revisión en la web (con `qa_admin`)

| # | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| QA-22 | Abrir el ticket QA-0001 | Historial con la toma, la llegada y los cambios de estado | |
| QA-23 | Abrir la orden de QA-0001 | Tarjeta "Registro en terreno": llegada verificada, fotos y firma | |
| QA-24 | Abrir la orden de QA-0002 | Llegada "fuera del radio" con la distancia | |

---

## 5. Si algo falla

Anotar en la columna "Resultado" qué pasó y, si se puede, guardar una captura
del emulador (botón de cámara de la barra lateral) en
[`capturas/`](capturas/). Cada falla confirmada se agrega como hallazgo en la
bitácora.
