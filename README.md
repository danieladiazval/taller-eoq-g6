# Simulador EOQ — Importación vs. proveedor local (Equipo G6)

App en Streamlit para el taller evaluativo EOQ: compara la importación en contenedor de 20',
la importación en contenedor de 40' y el proveedor local. Calcula el EOQ, la robustez del TRC,
la restricción de bodega, el Costo Total Anual y los puntos de equilibrio, y recomienda la mejor
alternativa físicamente factible.

## Requisito previo

Tener **Python 3.9 o superior** instalado ([python.org](https://www.python.org)).
En Windows, durante la instalación marca la casilla **"Add Python to PATH"**.

## Forma más fácil: doble clic

| Sistema | Archivo | Cómo abrirlo |
|---------|---------|--------------|
| Windows | `iniciar_app.bat` | Doble clic |
| macOS   | `iniciar_app.command` | Doble clic |

- La **primera vez** crea el entorno virtual e instala las dependencias (tarda unos minutos).
- Las **siguientes veces** solo levanta la app, que se abre en el navegador.
- Para detener la app, cierra la ventana negra (terminal).

**Notas para macOS:**
- Si al hacer doble clic aparece *"no se puede abrir porque proviene de un desarrollador
  no identificado"*: clic derecho sobre el archivo → **Abrir** → **Abrir**. Solo se pide la primera vez.
- Si el archivo perdió el permiso de ejecución (por ejemplo, al copiarlo desde un .zip),
  ejecuta una vez en la Terminal: `chmod +x iniciar_app.command`

**No copies la carpeta `.venv` entre Windows y Mac:** cada sistema necesita la suya.
Si pasas el proyecto de un computador a otro, borra `.venv` y el lanzador la vuelve a crear.

## Forma manual (terminal)

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

**macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Uso

La app abre con los datos de la pestaña **G6** ya cargados. Todos los parámetros se editan en la
barra lateral y los resultados se recalculan al instante.

- **Restablecer valores G6** vuelve a los datos originales.
- **Capacidad adicional de bodega** define qué puede usar una alternativa que no cabe en la
  bodega actual. En *automático* se compara alquiler contra ampliación y se toma la más barata que alcance.
- **Cargar datos desde el Excel del taller** (opcional) lee cualquier pestaña G1–G6 de
  `Datos_por_equipo_Taller_EOQ.xlsx`.

Pestañas, en el orden del video:

| Pestaña | Contenido (sección del taller) |
|---------|--------------------------------|
| 1. Datos y variables | Clasificación de la información y variables D, A, v, r (Etapa 1) |
| 2. EOQ y robustez | EOQ sin restricciones, cantidades reales, %ΔQ y penalización del TRC (Etapas 2 y 3, sección 11) |
| 3. Capacidad de bodega | Las cinco posibilidades de almacenamiento (Etapa 4) |
| 4. Comparativa | Tabla comparativa, factibilidad, alternativa recomendada y descarga en Excel (secciones 8 y 10) |
| 5. Gráficas | Diente de sierra en posiciones y curva TRC(Q) (sección 12) |
| 6. Sensibilidad y equilibrio | Precio máximo del proveedor local, financiación mínima del molde y barrido de parámetros (secciones 13 y 14) |
| 7. Preguntas de gerencia | Las tres variaciones del equipo G6, con botón para aplicarlas (Parte 4 del video) |

## Verificación contra cálculos manuales

`verificar_modelo.py` valida la app por etapas (sección 15 del taller), comparando cada resultado
contra cálculos hechos a mano y contra los valores del Excel del equipo:

```bash
.venv/bin/python verificar_modelo.py        # macOS, todas las etapas
.venv\Scripts\python verificar_modelo.py    # Windows
.venv/bin/python verificar_modelo.py 1 2    # solo algunas etapas
```
