# Simulador EOQ — Importación vs. proveedor local (Equipo G6)

App en Streamlit para decidir cómo abastecer una referencia de alta rotación: compara la
importación en contenedor de 20', la importación en contenedor de 40' y el proveedor local. Calcula el EOQ, la robustez del TRC,
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
- **Cargar datos desde el Excel de datos por equipo** (opcional) lee cualquier pestaña G1–G6 de
  `Datos_por_equipo_Taller_EOQ.xlsx`.

Pestañas, en el orden del video para la gerencia:

| Pestaña | Contenido |
|---------|-----------|
| 1. Datos y variables | Clasificación de cada dato (adquisición, ordenar, almacenar, capacidad, restricción física o no relevante) y construcción de D, A, v y r |
| 2. EOQ y robustez | EOQ sin restricciones de las tres alternativas, cantidades reales de contenedor (1.900 y 4.200), %ΔQ y penalización del TRC |
| 3. Capacidad de bodega | Posiciones requeridas y las cinco posibilidades: 20' y 40' con bodega actual o con alquiler/ampliación, y proveedor local |
| 4. Comparativa | Costo Total Anual por alternativa, factibilidad física, alternativa recomendada y descarga en Excel |
| 5. Gráficas | Diente de sierra en posiciones (un año en días, con línea de capacidad) y curva TRC(Q) con EOQ, 20' y 40' marcados |
| 6. Sensibilidad y equilibrio | Precio máximo competitivo del proveedor local, financiación mínima del molde y barrido de parámetros |
| 7. Preguntas de gerencia | Las tres variaciones del equipo G6, con botón para aplicarlas y ver si cambia la recomendación |

## Verificación contra cálculos manuales

`verificar_modelo.py` valida la app por etapas, en el mismo orden en que se construyó (funciones del
modelo, capacidad, escenarios, comparativa, interfaz, gráficas, sensibilidad y equilibrio), comparando
cada resultado contra cálculos hechos a mano y contra los valores del Excel del equipo:

```bash
.venv/bin/python verificar_modelo.py        # macOS, todas las etapas
.venv\Scripts\python verificar_modelo.py    # Windows
.venv/bin/python verificar_modelo.py 1 2    # solo algunas etapas
```
