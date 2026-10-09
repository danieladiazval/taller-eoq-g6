# Taller EOQ: simulador de decisión de abastecimiento (Equipo G6)

## Objetivo

Herramienta interactiva en **Streamlit** para decidir cómo abastecer una referencia de alta rotación:
importación en contenedor de 20', importación en contenedor de 40' o proveedor local.
La consigna completa está en `../Taller_EOQ.docx` y los datos en `../Datos_por_equipo_Taller_EOQ (1).xlsx`
(usar **solo la pestaña G6**; la pestaña `Preguntas_video_equipos` trae las preguntas de gerencia).

**Entregable de código:** `app.py` (un solo archivo, comentarios en español) + `requirements.txt`,
lanzadores `iniciar_app.bat` / `iniciar_app.command`, `README.md` y `verificar_modelo.py`.
El entregable principal del curso es un video de 5 minutos; la app es el soporte que se muestra.

## Supuestos del modelo (sección 2 de la consigna)

- Demanda determinística, uniforme y constante. Sin faltantes, sin tiempo de entrega, sin inventario de seguridad.
- Sin descuentos por cantidad. Cada escenario usa una sola fuente.
- Los contenedores van llenos: Q20 = 1.900 y Q40 = 4.200 unidades. El proveedor local pide su EOQ.
- Pedidos por año pueden ser no enteros. Una alternativa no factible nunca se recomienda.

## Variables (datos G6)

| Variable | Construcción | Valor G6 |
|----------|--------------|----------|
| D | Demanda anual | 11.500 u/año |
| A20 | Flete + aduana + transporte nacional + procesamiento (20') | $13.030.000 |
| A40 | Ídem (40') | $15.840.000 |
| ALocal | Transporte + recepción e inspección + procesamiento | $618.000 |
| v importado / v local | Costo unitario | $98.500 / $107.000 |
| r | Capital 20 % + seguro 2 % + deterioro 5 % + manejo 3 % | 30 % |

El costo de almacenar es **v·r** (no hay variable h). Precio de venta y publicidad no son relevantes para Q.

## Fórmulas

- EOQ: `Q* = sqrt(2AD / vr)`; TRC de inventarios: `TRC(Q) = A·D/Q + v·r·Q/2`.
- Posiciones = `ceil(inventario máximo / 25)`, con inventario máximo = Q.
- Capacidad: si no cabe en la bodega actual (65 pos.), se usa alquiler (+90, $20 M/año) o
  ampliación (+90, $10,5 M/año), la más barata que alcance. Si ninguna alcanza: no factible.
  El modo "ambas" (combinar alquiler + ampliación) es un análisis adicional, no parte de la consigna.
- Molde empresa = molde × (1 − p). Proveedor local factible solo si D ≤ 20.000 u/año.
- **Costo Total Anual** = vD + ordenar + almacenar + capacidad + molde (elige la alternativa).
- %ΔQ = (Qcont − EOQ)/EOQ; penalización = (TRC(Qcont) − TRC(EOQ))/TRC(EOQ).
- Precio máximo local: resolver `vD + sqrt(2·AL·D·r·v) + molde emp. + capacidad = costo de la mejor importación`.
- Financiación mínima: `p* = 1 − (objetivo − costo local sin molde) / molde`.

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

## Forma de trabajo (sección 15 de la consigna)

Construir y validar de forma progresiva: funciones → capacidad → escenarios → comparativa →
interfaz → gráficas → sensibilidad y equilibrio → validación manual. Cada cambio al modelo debe
pasar `python verificar_modelo.py` antes de darse por bueno; si cambian los valores esperados,
recalcularlos a mano (no copiarlos de la app).

## Restricciones técnicas

- Debe correr con **Python 3.9** (no usar `X | Y` en tipos ni `match`).
- Mismo estilo y lanzadores que el proyecto `App MotoTrack` (carpeta hermana): `.bat` con CRLF,
  `.command` con `chmod +x`, marca `.venv/instalado.ok`.
- Sin base de datos, sin login, sin despliegue. Errores con `st.error`, no tracebacks.
- Formato numérico colombiano: punto de miles, coma decimal.
