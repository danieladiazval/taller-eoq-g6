# Simulador EOQ: decisión de abastecimiento (Equipo G6)

## Contexto del caso

Una empresa colombiana comercializa una referencia de alta rotación con demanda anual conocida
(determinística, uniforme y constante). Hoy se abastece por **importación** en contenedores de
20' o 40': el de 40' reduce la frecuencia de importación, pero sube el inventario máximo y puede
superar la capacidad de bodega. También evalúa desarrollar un **proveedor local**: más flexible para
pedidos pequeños y frecuentes, pero con costo unitario mayor y un molde específico por desarrollar.

La gerencia pide evaluar las alternativas con una herramienta interactiva de apoyo a la decisión:
se cambian los parámetros de entrada y los resultados se recalculan solos, sin tocar código.

**Datos:** `../Datos_por_equipo_Taller_EOQ (1).xlsx`, **solo la pestaña G6**. La pestaña
`Preguntas_video_equipos` trae las tres preguntas de gerencia del equipo.

**Entregable de código:** `app.py` (un solo archivo, comentarios en español) + `requirements.txt`,
lanzadores `iniciar_app.bat` / `iniciar_app.command`, `README.md` y `verificar_modelo.py`.
El entregable principal es un video de 5 minutos; la app es el soporte que se muestra en él.

## Supuestos del modelo

- Demanda determinística, uniforme y constante; toda la demanda se atiende.
- Sin faltantes, tiempo de entrega, punto de reorden ni inventario de seguridad (no hay costo de agotado Cs).
- Sin descuentos por cantidad. Cada escenario usa una sola fuente (no se combinan local e importación).
- Los contenedores van llenos: Q20 = 1.900 y Q40 = 4.200 unidades. El proveedor local pide su EOQ.
- Los pedidos por año pueden ser un promedio no entero.
- Una alternativa físicamente no factible **nunca** se recomienda, aunque cueste menos.
- Los costos "equivalentes anuales" (molde, ampliación) ya vienen calculados; no se anualizan de nuevo.

## Etapas del análisis

1. **Clasificación y variables.** Clasificar cada dato de la hoja en: costo de adquisición, costo de
   ordenar, costo de almacenar, costos de capacidad, restricciones físicas o información no relevante
   para Q. Con eso construir D, A20, A40, ALocal, v (por alternativa) y r, explicando qué componentes
   suma cada una.
2. **EOQ sin restricciones** para 20', 40' y local: Q*, pedidos por año, inventario promedio, costo
   anual de ordenar, de almacenar y TRC. Es el benchmark económico.
3. **Cantidades reales de importación** (1.900 y 4.200): diferencia absoluta y porcentual frente al
   EOQ, TRC con la cantidad real y penalización absoluta y porcentual frente al TRC mínimo.
4. **Restricción de almacenamiento.** Cada posición guarda 25 unidades; las posiciones se calculan
   sobre el inventario máximo (justo al recibir). Validar si cada alternativa cabe en la bodega actual,
   necesita capacidad adicional (comparar alquiler vs. ampliación) o sigue sin caber. Aplica igual a
   20' y 40' (ninguno tiene cupo garantizado). Mostrar las cinco posibilidades: 20' + bodega actual,
   20' + alquiler/ampliación, 40' + bodega actual, 40' + alquiler/ampliación, proveedor local.
5. **Proveedor local.** Sin lote fijo: usa su EOQ. Considerar su mayor v, su menor A, el costo anual
   equivalente del molde y la proporción p que financia el proveedor.

## Variables (datos G6)

| Variable | Construcción | Valor G6 |
|----------|--------------|----------|
| D | Demanda anual | 11.500 u/año |
| A20 | Flete + aduana + transporte nacional + procesamiento (20') | $13.030.000 |
| A40 | Ídem (40') | $15.840.000 |
| ALocal | Transporte + recepción e inspección + procesamiento | $618.000 |
| v importado / v local | Costo unitario | $98.500 / $107.000 |
| r | Capital 20 % + seguro 2 % + deterioro 5 % + manejo 3 % | 30 % |

El costo de almacenar una unidad un año es **v·r** (no hay variable h). Precio de venta y
publicidad no son relevantes para Q.

## Fórmulas e indicadores

- EOQ: `Q* = sqrt(2AD / vr)`.
- **TRC de inventarios** = `A·D/Q + v·r·Q/2` (ordenar + almacenar). Sirve para analizar el Q.
- **Costo Total Anual** = vD + ordenar + almacenar + capacidad + molde (si aplica). Sirve para elegir
  la alternativa. La app debe mostrar los dos indicadores claramente separados.
- Posiciones = `ceil(inventario máximo / 25)`, con inventario máximo = Q.
- Capacidad: si no cabe en la bodega actual (65 pos.), se usa alquiler (+90, $20 M/año) o
  ampliación (+90, $10,5 M/año), la más barata que alcance. Si ninguna alcanza: no factible.
  El modo "ambas" (combinar alquiler + ampliación) es un análisis adicional, no un requisito.
- Molde empresa = molde × (1 − p). Proveedor local factible solo si D ≤ 20.000 u/año.
- Robustez (solo importadas): `%ΔQ = (Qcont − EOQ)/EOQ × 100`;
  `penalización TRC = (TRC(Qcont) − TRC(EOQ))/TRC(EOQ) × 100`. La idea es mostrar que una
  diferencia grande en cantidad no implica una diferencia grande en costo.
- Precio máximo local: resolver `vD + sqrt(2·AL·D·r·v) + molde emp. + capacidad = costo de la mejor importación`.
- Financiación mínima: `p* = 1 − (objetivo − costo local sin molde) / molde`.

## Requisitos de la app

**Por alternativa, calculado y mostrado automáticamente:** cantidad por pedido, EOQ de referencia,
pedidos por año, inventario promedio y máximo, posiciones requeridas, costo anual de adquisición,
ordenar y almacenar, TRC, costos de capacidad, costo del molde, Costo Total Anual y factibilidad
física. La alternativa recomendada (solo entre las factibles) debe destacarse.

**Visualizaciones obligatorias:**
- *Diente de sierra* en posiciones de almacenamiento para EOQ de referencia, 20', 40' y local,
  sobre un año en días (tasa de demanda = D/365), con una línea horizontal de capacidad que se
  actualiza al elegir alquiler o ampliación.
- *Curva TRC(Q)* marcando el EOQ y las cantidades de 20' y 40', para que se vea lo plana que es
  la curva cerca del mínimo.

**Sensibilidad.** Editables como mínimo: demanda anual, tasa de almacenamiento, v local, costo
anual de alquiler, costo anual equivalente de ampliación y % del molde financiado. Opcionales:
A20/A40, costo anual del molde, capacidad de bodega.

**Puntos de equilibrio.** (1) Precio unitario máximo del proveedor local antes de dejar de competir
con la mejor importación. (2) Porcentaje mínimo del molde que el proveedor tendría que financiar
para que el local sea competitivo.

## Video para la gerencia (orden de las pestañas)

Máximo 5 minutos, en un solo bloque sin cortes:
1. Apertura y clasificación de costos con las variables D, A, v, r.
2. Tabla comparativa de las tres alternativas, factibilidad y las dos gráficas obligatorias.
3. Recomendación sustentada en costo, factibilidad, comportamiento del inventario, sensibilidad y equilibrio.
4. Las tres preguntas de gerencia: cambiar el parámetro en la app, mostrar el nuevo resultado y
   explicar si la recomendación cambia y por qué.
5. Cierre ejecutivo.

## Resultados de referencia G6 (validados en `verificar_modelo.py`)

| Alternativa | Q | EOQ | Posiciones | Capacidad | Costo Total Anual |
|-------------|---|-----|------------|-----------|-------------------|
| Contenedor 20' | 1.900 | 3.184,6 | 76 | Ampliación $10,5 M | **$1.250.188.289** (recomendada) |
| Contenedor 40' | 4.200 | 3.511,3 | 168 | No cabe ni con 155 | $1.238.176.429 (no factible) |
| Proveedor local | 665,4 | 665,4 | 27 | Bodega actual | $1.287.860.463 |

- Penalización TRC: 20' = 13,64 % (con %ΔQ = −40,3 %); 40' = 1,61 % (con %ΔQ = +19,6 %).
- Precio máximo competitivo del local ≈ $103.753. Financiación mínima del molde ≈ 103,7 % (no alcanza ni con 100 %).
- Preguntas G6: v local $102.000 → cambia a local; v importado $105.000 → cambia a local;
  flete 20' $10 M → se mantiene 20' (1.267,6 M vs 1.287,9 M).

## Forma de trabajo

Construir y validar de forma progresiva, en este orden: funciones del modelo → restricción de
capacidad → escenarios → tabla comparativa → interfaz → gráficas → sensibilidad y equilibrio →
validación contra cálculos manuales. `verificar_modelo.py` sigue esas mismas etapas.
Cada cambio al modelo debe pasar `python verificar_modelo.py` antes de darse por bueno; si cambian
los valores esperados, recalcularlos a mano (no copiarlos de la app). Los resultados generados por
el agente se revisan antes de apoyarse en ellos para la recomendación.

## Restricciones técnicas

- Debe correr con **Python 3.9** (no usar `X | Y` en tipos ni `match`).
- Mismo estilo y lanzadores que el proyecto `App MotoTrack` (carpeta hermana): `.bat` con CRLF,
  `.command` con `chmod +x`, marca `.venv/instalado.ok`.
- Sin base de datos, sin login, sin despliegue. Errores con `st.error`, no tracebacks.
- Formato numérico colombiano: punto de miles, coma decimal.
