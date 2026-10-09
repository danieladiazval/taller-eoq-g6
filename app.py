# =============================================================================
# Simulador EOQ — Importación vs. proveedor local (Equipo G6)
# -----------------------------------------------------------------------------
# App de Streamlit que apoya la decisión de abastecimiento del taller EOQ:
#   1. Clasifica la información del caso y arma las variables D, A, v y r.
#   2. Calcula el EOQ sin restricciones de las tres alternativas
#      (contenedor 20', contenedor 40' y proveedor local).
#   3. Compara las cantidades reales de importación contra el EOQ (robustez).
#   4. Valida la capacidad de bodega (actual, alquiler o ampliación).
#   5. Calcula el Costo Total Anual y recomienda la mejor alternativa factible.
#   6. Muestra el diente de sierra, la curva TRC(Q), la sensibilidad,
#      los puntos de equilibrio y las preguntas de gerencia del video.
#
# Para correrla:  streamlit run app.py
# =============================================================================

import io
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# Constantes generales
# -----------------------------------------------------------------------------

# Catálogo de la información del caso (pestaña G6 del Excel del taller).
# Cada entrada tiene:
#   clave      -> nombre corto que usa el modelo
#   etiqueta   -> texto exacto de la columna A del Excel (sirve para cargarlo)
#   unidad     -> unidad que se muestra en la app
#   clase      -> clasificación de la Etapa 1
#   grupo      -> sección de la barra lateral donde se edita
#   tipo       -> "int" (cantidades y pesos) o "pct" (porcentajes, se editan en %)
#   valor      -> valor del equipo G6 (los porcentajes van en %, p. ej. 20.0)
CATALOGO = [
    # --- Demanda y almacenamiento ---
    dict(clave="D", etiqueta="Demanda anual proyectada", unidad="unidades/año",
         clase="Demanda (variable D)", grupo="Demanda y almacenamiento", tipo="int", valor=11500),
    dict(clave="r_capital", etiqueta="Costo de capital", unidad="% anual de v",
         clase="Costo de almacenar", grupo="Demanda y almacenamiento", tipo="pct", valor=20.0),
    dict(clave="r_seguro", etiqueta="Seguro del inventario", unidad="% anual de v",
         clase="Costo de almacenar", grupo="Demanda y almacenamiento", tipo="pct", valor=2.0),
    dict(clave="r_deterioro", etiqueta="Riesgo de deterioro y obsolescencia", unidad="% anual de v",
         clase="Costo de almacenar", grupo="Demanda y almacenamiento", tipo="pct", valor=5.0),
    dict(clave="r_manejo", etiqueta="Manejo y otros costos relacionados con inventario", unidad="% anual de v",
         clase="Costo de almacenar", grupo="Demanda y almacenamiento", tipo="pct", valor=3.0),
    # --- Importación ---
    dict(clave="v_imp", etiqueta="Costo unitario producto importado", unidad="$/unidad",
         clase="Costo de adquisición", grupo="Importación", tipo="int", valor=98500),
    dict(clave="cap_20", etiqueta="Capacidad contenedor 20'", unidad="unidades",
         clase="Restricción física", grupo="Importación", tipo="int", valor=1900),
    dict(clave="cap_40", etiqueta="Capacidad contenedor 40'", unidad="unidades",
         clase="Restricción física", grupo="Importación", tipo="int", valor=4200),
    dict(clave="flete_20", etiqueta="Flete internacional contenedor 20'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=7130000),
    dict(clave="flete_40", etiqueta="Flete internacional contenedor 40'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=8640000),
    dict(clave="aduana_20", etiqueta="Gestión aduanera y portuaria contenedor 20'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=2200000),
    dict(clave="aduana_40", etiqueta="Gestión aduanera y portuaria contenedor 40'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=2500000),
    dict(clave="transp_20", etiqueta="Transporte nacional contenedor 20'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=3000000),
    dict(clave="transp_40", etiqueta="Transporte nacional contenedor 40'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=4000000),
    dict(clave="proc_20", etiqueta="Procesamiento administrativo contenedor 20'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=700000),
    dict(clave="proc_40", etiqueta="Procesamiento administrativo contenedor 40'", unidad="$/importación",
         clase="Costo de ordenar", grupo="Importación", tipo="int", valor=700000),
    # --- Bodega ---
    dict(clave="und_posicion", etiqueta="Unidades por posición de almacenamiento", unidad="unidades/posición",
         clase="Restricción física", grupo="Bodega", tipo="int", valor=25),
    dict(clave="pos_actual", etiqueta="Capacidad actual disponible en bodega", unidad="posiciones",
         clase="Restricción física", grupo="Bodega", tipo="int", valor=65),
    dict(clave="pos_alquiler", etiqueta="Capacidad adicional mediante alquiler", unidad="posiciones",
         clase="Restricción física", grupo="Bodega", tipo="int", valor=90),
    dict(clave="costo_alquiler", etiqueta="Costo anual del alquiler", unidad="$/año",
         clase="Costo asociado a capacidad", grupo="Bodega", tipo="int", valor=20000000),
    dict(clave="pos_ampliacion", etiqueta="Capacidad adicional mediante ampliación", unidad="posiciones",
         clase="Restricción física", grupo="Bodega", tipo="int", valor=90),
    dict(clave="costo_ampliacion", etiqueta="Costo anual equivalente de ampliación", unidad="$/año",
         clase="Costo asociado a capacidad", grupo="Bodega", tipo="int", valor=10500000),
    # --- Proveedor local ---
    dict(clave="v_local", etiqueta="Costo unitario proveedor local", unidad="$/unidad",
         clase="Costo de adquisición", grupo="Proveedor local", tipo="int", valor=107000),
    dict(clave="transp_local", etiqueta="Transporte proveedor local", unidad="$/pedido",
         clase="Costo de ordenar", grupo="Proveedor local", tipo="int", valor=360000),
    dict(clave="recep_local", etiqueta="Recepción e inspección proveedor local", unidad="$/pedido",
         clase="Costo de ordenar", grupo="Proveedor local", tipo="int", valor=155000),
    dict(clave="proc_local", etiqueta="Procesamiento administrativo proveedor local", unidad="$/pedido",
         clase="Costo de ordenar", grupo="Proveedor local", tipo="int", valor=103000),
    dict(clave="cap_anual_local", etiqueta="Capacidad anual proveedor local", unidad="unidades/año",
         clase="Restricción física", grupo="Proveedor local", tipo="int", valor=20000),
    dict(clave="molde", etiqueta="Costo anual equivalente del molde", unidad="$/año",
         clase="Costo asociado a capacidad (molde)", grupo="Proveedor local", tipo="int", valor=45000000),
    dict(clave="p_molde", etiqueta="Porcentaje del molde financiado por el proveedor", unidad="%",
         clase="Costo asociado a capacidad (molde)", grupo="Proveedor local", tipo="pct", valor=20.0),
    # --- Información no relevante para Q ---
    dict(clave="precio_venta", etiqueta="Precio de venta", unidad="$/unidad",
         clase="Información no relevante", grupo="Información no relevante", tipo="int", valor=148000),
    dict(clave="publicidad", etiqueta="Presupuesto anual de publicidad del producto", unidad="$/año",
         clase="Información no relevante", grupo="Información no relevante", tipo="int", valor=24000000),
]
CATALOGO_POR_CLAVE = {c["clave"]: c for c in CATALOGO}

# Orden de las secciones de la barra lateral y de las clases de la Etapa 1.
GRUPOS = ["Demanda y almacenamiento", "Importación", "Bodega", "Proveedor local", "Información no relevante"]
ORDEN_CLASES = [
    "Demanda (variable D)",
    "Costo de adquisición",
    "Costo de ordenar",
    "Costo de almacenar",
    "Costo asociado a capacidad",
    "Costo asociado a capacidad (molde)",
    "Restricción física",
    "Información no relevante",
]

# Nombres de las alternativas, en el orden en que se muestran.
ALT_20 = "Contenedor 20'"
ALT_40 = "Contenedor 40'"
ALT_LOCAL = "Proveedor local"
ALTERNATIVAS = [ALT_20, ALT_40, ALT_LOCAL]
ALT_IMPORTADAS = [ALT_20, ALT_40]

# Colores de cada alternativa en las gráficas (paleta categórica validada).
COLORES = {
    ALT_20: "#2a78d6",
    ALT_40: "#eb6834",
    ALT_LOCAL: "#1baf7a",
    "EOQ de referencia": "#4a3aa7",
}
COLOR_TEXTO = "#1F2328"
COLOR_SECUNDARIO = "#52514e"
COLOR_LIMITE = "#d03b3b"

# Fuentes de capacidad adicional que se pueden elegir en la barra lateral.
MODOS_CAPACIDAD = {
    "auto": "Automático: la opción más barata que alcance",
    "actual": "Solo bodega actual",
    "alquiler": "Bodega actual + alquiler",
    "ampliacion": "Bodega actual + ampliación",
    "ambas": "Automático, permitiendo combinar alquiler + ampliación (análisis adicional)",
}

# Preguntas de gerencia del equipo G6 (pestaña "Preguntas_video_equipos").
# Los valores están en las mismas unidades que se editan en la barra lateral.
PREGUNTAS_G6 = [
    dict(
        titulo="Variación 1 — Precio del proveedor local",
        texto="En una negociación agresiva por quedarse con el contrato, el proveedor local ofrece bajar "
              "su precio de $107.000 a $102.000 por unidad. ¿Cambia esto la recomendación?",
        clave="v_local", antes=107000, despues=102000,
    ),
    dict(
        titulo="Variación 2 — Arancel al producto importado",
        texto="El gobierno anuncia un nuevo arancel que sube el costo unitario del producto importado "
              "de $98.500 a $105.000. ¿Cambia esto la recomendación?",
        clave="v_imp", antes=98500, despues=105000,
    ),
    dict(
        titulo="Variación 3 — Flete del contenedor de 20'",
        texto="Una crisis en el transporte marítimo hace que el flete internacional del contenedor de 20' "
              "suba de $7.130.000 a $10.000.000 por importación. ¿Cambia esto la recomendación?",
        clave="flete_20", antes=7130000, despues=10000000,
    ),
]

# Parámetros que se pueden barrer en el análisis de sensibilidad.
PARAMETROS_SENSIBILIDAD = [
    "D", "r_capital", "v_local", "costo_alquiler", "costo_ampliacion", "p_molde",
    "v_imp", "flete_20", "flete_40", "molde", "pos_actual", "transp_local",
]

DIAS_ANIO = 365


# -----------------------------------------------------------------------------
# 1. Formato de números (estilo colombiano: punto de miles, coma decimal)
# -----------------------------------------------------------------------------

def numero(x, decimales=0):
    """Formatea un número con punto de miles y coma decimal."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    texto = f"{x:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pesos(x, decimales=0):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    signo = "-" if x < 0 else ""
    return f"{signo}${numero(abs(x), decimales)}"


def porcentaje(x, decimales=1):
    """Recibe una fracción (0.2) y la muestra como 20,0 %."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{numero(x * 100, decimales)} %"


def millones(x):
    return f"${numero(x / 1e6, 2)} M"


def md(texto):
    """Escapa el signo $ para los textos que Streamlit muestra como markdown.
    Sin esto, el texto entre dos $ se interpreta como fórmula LaTeX.
    """
    return texto.replace("$", r"\$")


# -----------------------------------------------------------------------------
# 2. Modelo EOQ
# -----------------------------------------------------------------------------

def calcular_variables(p):
    """Arma las variables del modelo a partir de la información del caso:
    D, A20, A40, ALocal, v (importado y local) y r.
    """
    return {
        "D": p["D"],
        "A20": p["flete_20"] + p["aduana_20"] + p["transp_20"] + p["proc_20"],
        "A40": p["flete_40"] + p["aduana_40"] + p["transp_40"] + p["proc_40"],
        "AL": p["transp_local"] + p["recep_local"] + p["proc_local"],
        "v_imp": p["v_imp"],
        "v_local": p["v_local"],
        "r": p["r_capital"] + p["r_seguro"] + p["r_deterioro"] + p["r_manejo"],
    }


def eoq(A, D, v, r):
    """Cantidad económica de pedido: Q* = raíz(2AD / vr)."""
    return math.sqrt(2 * A * D / (v * r))


def trc(Q, A, D, v, r):
    """TRC de inventarios = costo de ordenar + costo de almacenar."""
    return A * D / Q + v * r * Q / 2


def posiciones_requeridas(inventario_maximo, unidades_por_posicion):
    """Posiciones que ocupa el inventario máximo (justo después de recibir).
    Se resta un margen mínimo para que 1900/25 = 76 no se vuelva 77 por redondeo.
    """
    return math.ceil(inventario_maximo / unidades_por_posicion - 1e-9)


def opciones_capacidad(p, modo):
    """Fuentes de capacidad adicional permitidas: (nombre, capacidad total, costo anual)."""
    actual = p["pos_actual"]
    alquiler = ("Alquiler", actual + p["pos_alquiler"], p["costo_alquiler"])
    ampliacion = ("Ampliación", actual + p["pos_ampliacion"], p["costo_ampliacion"])
    ambas = ("Alquiler + ampliación", actual + p["pos_alquiler"] + p["pos_ampliacion"],
             p["costo_alquiler"] + p["costo_ampliacion"])
    return {
        "auto": [alquiler, ampliacion],
        "actual": [],
        "alquiler": [alquiler],
        "ampliacion": [ampliacion],
        "ambas": [alquiler, ampliacion, ambas],
    }[modo]


def evaluar_capacidad(posiciones, p, modo):
    """Decide con qué bodega se atiende una política y cuánto cuesta.
    Si cabe en la bodega actual no se paga capacidad adicional; si no cabe,
    se toma la opción permitida más barata que alcance. Si ninguna alcanza,
    la alternativa no es factible.
    """
    actual = p["pos_actual"]
    if posiciones <= actual:
        return {"opcion": "Bodega actual", "capacidad": actual, "costo": 0.0, "cabe": True}

    opciones = opciones_capacidad(p, modo)
    sirven = [o for o in opciones if posiciones <= o[1]]
    if sirven:
        nombre, capacidad, costo = min(sirven, key=lambda o: o[2])
        return {"opcion": nombre, "capacidad": capacidad, "costo": float(costo), "cabe": True}

    # Ninguna opción alcanza: se reporta la mayor capacidad que se intentó.
    if opciones:
        capacidad = max(o[1] for o in opciones)
        nombres = " o ".join(o[0].lower() for o in opciones if o[1] == capacidad).capitalize()
        return {"opcion": f"{nombres} (no alcanza)", "capacidad": capacidad, "costo": 0.0, "cabe": False}
    return {"opcion": "Bodega actual (no alcanza)", "capacidad": actual, "costo": 0.0, "cabe": False}


def evaluar_alternativa(nombre, Q, Q_eoq, A, v, var, p, modo):
    """Calcula todos los indicadores de una alternativa con cantidad por pedido Q."""
    D, r = var["D"], var["r"]
    es_local = nombre == ALT_LOCAL

    posiciones = posiciones_requeridas(Q, p["und_posicion"])
    capacidad = evaluar_capacidad(posiciones, p, modo)
    proveedor_ok = (D <= p["cap_anual_local"]) if es_local else True

    adquisicion = v * D
    ordenar = A * D / Q
    almacenar = v * r * Q / 2
    costo_molde = p["molde"] * (1 - p["p_molde"]) if es_local else 0.0
    costo_total = adquisicion + ordenar + almacenar + capacidad["costo"] + costo_molde

    motivos = []
    if not capacidad["cabe"]:
        motivos.append(
            f"requiere {posiciones} posiciones y la capacidad máxima disponible es {capacidad['capacidad']}"
        )
    if not proveedor_ok:
        motivos.append(
            f"la demanda ({numero(D)}) supera la capacidad anual del proveedor ({numero(p['cap_anual_local'])})"
        )

    return {
        "alternativa": nombre,
        "Q": Q,
        "EOQ": Q_eoq,
        "A": A,
        "v": v,
        "pedidos_anio": D / Q,
        "ciclo_dias": Q / (D / DIAS_ANIO),
        "inv_promedio": Q / 2,
        "inv_maximo": Q,
        "posiciones": posiciones,
        "opcion_capacidad": capacidad["opcion"],
        "capacidad_disponible": capacidad["capacidad"],
        "costo_adquisicion": adquisicion,
        "costo_ordenar": ordenar,
        "costo_almacenar": almacenar,
        "TRC": ordenar + almacenar,
        "TRC_EOQ": trc(Q_eoq, A, D, v, r),
        "costo_capacidad": capacidad["costo"],
        "costo_molde": costo_molde,
        "costo_total": costo_total,
        "factible": capacidad["cabe"] and proveedor_ok,
        "motivo": "; ".join(motivos),
    }


def evaluar_todo(p, modo):
    """Evalúa las tres alternativas y elige la recomendada (la factible más barata)."""
    var = calcular_variables(p)
    D, r = var["D"], var["r"]

    eoq_20 = eoq(var["A20"], D, var["v_imp"], r)
    eoq_40 = eoq(var["A40"], D, var["v_imp"], r)
    eoq_local = eoq(var["AL"], D, var["v_local"], r)

    resultados = {
        # Los contenedores se usan llenos: la cantidad por pedido es la capacidad del contenedor.
        ALT_20: evaluar_alternativa(ALT_20, p["cap_20"], eoq_20, var["A20"], var["v_imp"], var, p, modo),
        ALT_40: evaluar_alternativa(ALT_40, p["cap_40"], eoq_40, var["A40"], var["v_imp"], var, p, modo),
        # El proveedor local no tiene lote fijo: pide directamente el EOQ.
        ALT_LOCAL: evaluar_alternativa(ALT_LOCAL, eoq_local, eoq_local, var["AL"], var["v_local"], var, p, modo),
    }

    factibles = [res for res in resultados.values() if res["factible"]]
    recomendada = min(factibles, key=lambda res: res["costo_total"]) if factibles else None
    importadas = [resultados[a] for a in ALT_IMPORTADAS if resultados[a]["factible"]]
    mejor_importacion = min(importadas, key=lambda res: res["costo_total"]) if importadas else None

    return {
        "var": var,
        "resultados": resultados,
        "recomendada": recomendada,
        "mejor_importacion": mejor_importacion,
    }


def precio_maximo_local(p, modo, objetivo, financiacion=None):
    """Costo unitario máximo del proveedor local para igualar el costo total `objetivo`.

    Costo total local(v) = vD + raíz(2·A·D·r·v) + molde empresa + capacidad.
    Con x = raíz(v) queda una ecuación cuadrática: D·x² + b·x + c = 0.
    `financiacion` permite calcularlo con otro porcentaje del molde financiado.
    """
    p = dict(p)
    if financiacion is not None:
        p["p_molde"] = financiacion
    var = calcular_variables(p)
    D, r, AL = var["D"], var["r"], var["AL"]
    molde_empresa = p["molde"] * (1 - p["p_molde"])
    costo_capacidad = evaluar_todo(p, modo)["resultados"][ALT_LOCAL]["costo_capacidad"]

    # La capacidad depende del EOQ (que cambia con v): se ajusta una segunda vez si hace falta.
    v_max, local = None, None
    for _ in range(3):
        b = math.sqrt(2 * AL * D * r)
        c = molde_empresa + costo_capacidad - objetivo
        if c >= 0:
            # Ni regalando el producto alcanza: los costos fijos ya superan el objetivo.
            return None, None
        x = (-b + math.sqrt(b * b - 4 * D * c)) / (2 * D)
        v_max = x * x
        local = evaluar_todo(dict(p, v_local=v_max), modo)["resultados"][ALT_LOCAL]
        if abs(local["costo_capacidad"] - costo_capacidad) < 1e-6:
            break
        costo_capacidad = local["costo_capacidad"]
    return v_max, local


def financiacion_minima(p, modo, objetivo):
    """Porcentaje mínimo del molde que debe financiar el proveedor para igualar `objetivo`."""
    if p["molde"] <= 0:
        return None
    local = evaluar_todo(p, modo)["resultados"][ALT_LOCAL]
    costo_sin_molde = local["costo_total"] - local["costo_molde"]
    return 1 - (objetivo - costo_sin_molde) / p["molde"]


# -----------------------------------------------------------------------------
# 3. Parámetros: valores por defecto, lectura de la barra lateral y del Excel
# -----------------------------------------------------------------------------

def clave_estado(clave):
    return f"par_{clave}"


def valor_por_defecto(c):
    return float(c["valor"]) if c["tipo"] == "pct" else int(c["valor"])


def iniciar_estado():
    """Carga los valores del equipo G6 la primera vez que se abre la app."""
    for c in CATALOGO:
        st.session_state.setdefault(clave_estado(c["clave"]), valor_por_defecto(c))
    st.session_state.setdefault("modo_capacidad", "auto")


def restablecer_g6():
    for c in CATALOGO:
        st.session_state[clave_estado(c["clave"])] = valor_por_defecto(c)
    st.session_state["modo_capacidad"] = "auto"
    st.session_state["mensaje_excel"] = ("ok", "Se restablecieron los valores de la pestaña G6.")


def fijar_parametro(clave, valor):
    """Callback de los botones que cambian un parámetro (preguntas de gerencia)."""
    c = CATALOGO_POR_CLAVE[clave]
    st.session_state[clave_estado(clave)] = float(valor) if c["tipo"] == "pct" else int(valor)


def leer_parametros():
    """Devuelve los parámetros en unidades del modelo (porcentajes como fracción)."""
    p = {}
    for c in CATALOGO:
        valor = st.session_state[clave_estado(c["clave"])]
        p[c["clave"]] = valor / 100 if c["tipo"] == "pct" else valor
    return p


def cargar_desde_excel():
    """Lee la pestaña elegida del Excel del taller y copia sus valores a la barra lateral.
    Busca cada dato por el texto de la columna A y toma el valor de la columna C.
    """
    archivo = st.session_state.get("archivo_excel")
    hoja = st.session_state.get("hoja_excel")
    if archivo is None or hoja is None:
        st.session_state["mensaje_excel"] = ("error", "Primero sube el Excel y elige una pestaña.")
        return
    try:
        crudo = pd.read_excel(io.BytesIO(archivo.getvalue()), sheet_name=hoja, header=None)
    except Exception as e:  # noqa: BLE001 - se muestra el error al usuario
        st.session_state["mensaje_excel"] = ("error", f"No se pudo leer la pestaña '{hoja}': {e}")
        return

    por_etiqueta = {c["etiqueta"].lower(): c for c in CATALOGO}
    encontrados = set()
    for _, fila in crudo.iterrows():
        if len(fila) < 3:
            continue
        etiqueta = str(fila.iloc[0]).strip().lower()
        valor = fila.iloc[2]
        c = por_etiqueta.get(etiqueta)
        if c is None or c["clave"] in encontrados:
            continue
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            continue
        if math.isnan(valor):
            continue
        # En el Excel los porcentajes vienen como fracción (0.2 = 20 %).
        st.session_state[clave_estado(c["clave"])] = round(valor * 100, 4) if c["tipo"] == "pct" else int(round(valor))
        encontrados.add(c["clave"])

    faltantes = [c["etiqueta"] for c in CATALOGO if c["clave"] not in encontrados]
    if not encontrados:
        st.session_state["mensaje_excel"] = (
            "error", f"La pestaña '{hoja}' no tiene el formato esperado (datos en columnas A y C).")
    elif faltantes:
        st.session_state["mensaje_excel"] = (
            "aviso", f"Se cargaron {len(encontrados)} datos de '{hoja}'. No se encontraron: {', '.join(faltantes)}.")
    else:
        st.session_state["mensaje_excel"] = ("ok", f"Se cargaron los {len(encontrados)} datos de la pestaña '{hoja}'.")


def nombre_parametro(clave):
    c = CATALOGO_POR_CLAVE[clave]
    return f"{c['etiqueta']} ({c['unidad']})"


# -----------------------------------------------------------------------------
# 4. Tablas
# -----------------------------------------------------------------------------

def formatear(df, formatos):
    """Copia del DataFrame con las columnas indicadas convertidas a texto con formato."""
    salida = df.copy()
    for columna, funcion in formatos.items():
        salida[columna] = salida[columna].map(funcion)
    return salida


def tabla_clasificacion(p):
    filas = []
    for c in CATALOGO:
        valor = p[c["clave"]]
        filas.append({
            "Información": c["etiqueta"],
            "Unidad": c["unidad"],
            "Valor": porcentaje(valor) if c["tipo"] == "pct" else numero(valor),
            "Clasificación": c["clase"],
        })
    df = pd.DataFrame(filas)
    df["orden"] = df["Clasificación"].map(ORDEN_CLASES.index)
    return df.sort_values("orden", kind="stable").drop(columns="orden")


def tabla_variables(var):
    return pd.DataFrame([
        {"Variable": "D", "Descripción": "Demanda anual", "Valor": var["D"], "Unidad": "unidades/año",
         "Componentes": "Demanda anual proyectada"},
        {"Variable": "A20", "Descripción": "Costo de ordenar contenedor 20'", "Valor": var["A20"],
         "Unidad": "$/importación",
         "Componentes": "Flete internacional + gestión aduanera y portuaria + transporte nacional + procesamiento administrativo (20')"},
        {"Variable": "A40", "Descripción": "Costo de ordenar contenedor 40'", "Valor": var["A40"],
         "Unidad": "$/importación",
         "Componentes": "Flete internacional + gestión aduanera y portuaria + transporte nacional + procesamiento administrativo (40')"},
        {"Variable": "ALocal", "Descripción": "Costo de ordenar proveedor local", "Valor": var["AL"],
         "Unidad": "$/pedido",
         "Componentes": "Transporte + recepción e inspección + procesamiento administrativo"},
        {"Variable": "v importado", "Descripción": "Costo unitario importado", "Valor": var["v_imp"],
         "Unidad": "$/unidad", "Componentes": "Costo unitario producto importado"},
        {"Variable": "v local", "Descripción": "Costo unitario proveedor local", "Valor": var["v_local"],
         "Unidad": "$/unidad", "Componentes": "Costo unitario proveedor local"},
        {"Variable": "r", "Descripción": "Tasa anual de almacenamiento", "Valor": var["r"],
         "Unidad": "% anual de v",
         "Componentes": "Costo de capital + seguro + deterioro y obsolescencia + manejo"},
        {"Variable": "v·r importado", "Descripción": "Costo de almacenar 1 unidad un año", "Valor": var["v_imp"] * var["r"],
         "Unidad": "$/unidad-año", "Componentes": "v importado × r"},
        {"Variable": "v·r local", "Descripción": "Costo de almacenar 1 unidad un año", "Valor": var["v_local"] * var["r"],
         "Unidad": "$/unidad-año", "Componentes": "v local × r"},
    ])


def formatear_variables(df):
    salida = df.copy()
    salida["Valor"] = [
        porcentaje(v) if var == "r" else (numero(v) if var == "D" else pesos(v))
        for var, v in zip(df["Variable"], df["Valor"])
    ]
    return salida


def tabla_eoq(evaluacion):
    """Etapa 2: EOQ sin restricciones (benchmark económico)."""
    var = evaluacion["var"]
    filas = []
    for nombre in ALTERNATIVAS:
        res = evaluacion["resultados"][nombre]
        Q = res["EOQ"]
        filas.append({
            "Alternativa": nombre,
            "A ($/pedido)": res["A"],
            "v ($/unidad)": res["v"],
            "EOQ Q* (unidades)": Q,
            "Pedidos por año": var["D"] / Q,
            "Inventario promedio": Q / 2,
            "Costo anual de ordenar": res["A"] * var["D"] / Q,
            "Costo anual de almacenar": res["v"] * var["r"] * Q / 2,
            "TRC(Q*)": res["TRC_EOQ"],
        })
    return pd.DataFrame(filas)


FORMATO_EOQ = {
    "A ($/pedido)": pesos, "v ($/unidad)": pesos,
    "EOQ Q* (unidades)": lambda x: numero(x, 1), "Pedidos por año": lambda x: numero(x, 2),
    "Inventario promedio": lambda x: numero(x, 1), "Costo anual de ordenar": pesos,
    "Costo anual de almacenar": pesos, "TRC(Q*)": pesos,
}


def tabla_robustez(evaluacion):
    """Etapa 3 / sección 11: cantidad real del contenedor frente al EOQ."""
    filas = []
    for nombre in ALT_IMPORTADAS:
        res = evaluacion["resultados"][nombre]
        filas.append({
            "Alternativa": nombre,
            "Q contenedor": res["Q"],
            "EOQ": res["EOQ"],
            "ΔQ (unidades)": res["Q"] - res["EOQ"],
            "%ΔQ": (res["Q"] - res["EOQ"]) / res["EOQ"],
            "TRC(Q contenedor)": res["TRC"],
            "TRC(EOQ)": res["TRC_EOQ"],
            "ΔTRC": res["TRC"] - res["TRC_EOQ"],
            "Penalización TRC": (res["TRC"] - res["TRC_EOQ"]) / res["TRC_EOQ"],
        })
    return pd.DataFrame(filas)


FORMATO_ROBUSTEZ = {
    "Q contenedor": numero, "EOQ": lambda x: numero(x, 1), "ΔQ (unidades)": lambda x: numero(x, 1),
    "%ΔQ": porcentaje, "TRC(Q contenedor)": pesos, "TRC(EOQ)": pesos, "ΔTRC": pesos,
    "Penalización TRC": lambda x: porcentaje(x, 2),
}


def tabla_penalizacion_generica():
    """Penalización del TRC cuando se pide k veces el EOQ: ½(k + 1/k) − 1."""
    ks = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0]
    return pd.DataFrame({
        "Q / EOQ": [numero(k, 1) for k in ks],
        "%ΔQ": [porcentaje(k - 1, 0) for k in ks],
        "Penalización TRC": [porcentaje(0.5 * (k + 1 / k) - 1, 1) for k in ks],
    })


def tabla_cinco_escenarios(evaluacion, p):
    """Etapa 4: las cinco posibilidades de almacenamiento que pide la consigna."""
    filas = []

    def fila(escenario, posiciones, capacidad, cabe, costo, resultado):
        filas.append({
            "Escenario": escenario,
            "Posiciones requeridas": posiciones,
            "Capacidad disponible (posiciones)": capacidad,
            "¿Cabe?": "Sí" if cabe else "No",
            "Costo anual de capacidad": costo,
            "Resultado": resultado,
        })

    actual = p["pos_actual"]
    for nombre in ALT_IMPORTADAS:
        res = evaluacion["resultados"][nombre]
        pos = res["posiciones"]
        cabe_actual = pos <= actual
        fila(f"{nombre} + bodega actual", pos, actual, cabe_actual, 0.0,
             "Factible sin costo adicional" if cabe_actual else "No cabe: requiere capacidad adicional")

        if cabe_actual:
            fila(f"{nombre} + alquiler o ampliación", pos, None, True, None,
                 "No se requiere: ya cabe en la bodega actual")
            continue
        opciones = opciones_capacidad(p, "auto")
        sirven = [o for o in opciones if pos <= o[1]]
        detalle = " · ".join(f"{n}: {c} pos., {pesos(k)}/año" for n, c, k in opciones)
        if sirven:
            elegida = min(sirven, key=lambda o: o[2])
            fila(f"{nombre} + alquiler o ampliación", pos, elegida[1], True, float(elegida[2]),
                 f"Factible con {elegida[0].lower()} (la más barata que alcanza). {detalle}")
        else:
            maxima = max(o[1] for o in opciones)
            fila(f"{nombre} + alquiler o ampliación", pos, maxima, False, None,
                 f"No factible ni con capacidad adicional. {detalle}")

    local = evaluacion["resultados"][ALT_LOCAL]
    pos = local["posiciones"]
    cabe_actual = pos <= actual
    if cabe_actual:
        fila(ALT_LOCAL, pos, actual, True, 0.0, "Factible en la bodega actual")
    else:
        cap = evaluar_capacidad(pos, p, "auto")
        fila(ALT_LOCAL, pos, cap["capacidad"], cap["cabe"], cap["costo"] if cap["cabe"] else None,
             f"Requiere {cap['opcion'].lower()}" if cap["cabe"] else "No factible ni con capacidad adicional")
    return pd.DataFrame(filas)


FORMATO_ESCENARIOS = {
    "Capacidad disponible (posiciones)": lambda x: "—" if x is None or pd.isna(x) else numero(x),
    "Costo anual de capacidad": lambda x: "—" if x is None or pd.isna(x) else pesos(x),
}


def tabla_comparativa(evaluacion):
    """Tabla comparativa: una columna por alternativa, una fila por indicador."""
    filas = [
        ("Cantidad por pedido (Q)", lambda r: numero(r["Q"], 1), "Q"),
        ("EOQ de referencia", lambda r: numero(r["EOQ"], 1), "EOQ"),
        ("Pedidos promedio por año", lambda r: numero(r["pedidos_anio"], 2), "pedidos_anio"),
        ("Duración del ciclo (días)", lambda r: numero(r["ciclo_dias"], 1), "ciclo_dias"),
        ("Inventario promedio (unidades)", lambda r: numero(r["inv_promedio"], 1), "inv_promedio"),
        ("Inventario máximo (unidades)", lambda r: numero(r["inv_maximo"], 1), "inv_maximo"),
        ("Posiciones requeridas", lambda r: numero(r["posiciones"]), "posiciones"),
        ("Bodega utilizada", lambda r: r["opcion_capacidad"], "opcion_capacidad"),
        ("Capacidad disponible (posiciones)", lambda r: numero(r["capacidad_disponible"]), "capacidad_disponible"),
        ("Costo anual de adquisición (vD)", lambda r: pesos(r["costo_adquisicion"]), "costo_adquisicion"),
        ("Costo anual de ordenar", lambda r: pesos(r["costo_ordenar"]), "costo_ordenar"),
        ("Costo anual de almacenar", lambda r: pesos(r["costo_almacenar"]), "costo_almacenar"),
        ("TRC de inventarios", lambda r: pesos(r["TRC"]), "TRC"),
        ("Costo de capacidad", lambda r: pesos(r["costo_capacidad"]), "costo_capacidad"),
        ("Costo del molde (empresa)", lambda r: pesos(r["costo_molde"]), "costo_molde"),
        ("Costo Total Anual", lambda r: pesos(r["costo_total"]), "costo_total"),
        ("Factibilidad física", lambda r: "Factible" if r["factible"] else f"No factible: {r['motivo']}", "factible"),
    ]
    texto = {"Indicador": [f[0] for f in filas]}
    numerico = {"Indicador": [f[0] for f in filas]}
    for nombre in ALTERNATIVAS:
        res = evaluacion["resultados"][nombre]
        texto[nombre] = [f[1](res) for f in filas]
        numerico[nombre] = [res[f[2]] for f in filas]
    return pd.DataFrame(texto), pd.DataFrame(numerico)


def excel_resultados(p, evaluacion, modo):
    """Arma un Excel con los parámetros y todas las tablas de resultados."""
    parametros = pd.DataFrame([
        {"Información": c["etiqueta"], "Unidad": c["unidad"], "Valor": p[c["clave"]], "Clasificación": c["clase"]}
        for c in CATALOGO
    ])
    parametros.loc[len(parametros)] = ["Fuente de capacidad adicional", "", MODOS_CAPACIDAD[modo], ""]
    _, comparativa = tabla_comparativa(evaluacion)

    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        parametros.to_excel(writer, sheet_name="Parametros", index=False)
        tabla_variables(evaluacion["var"]).to_excel(writer, sheet_name="Variables", index=False)
        tabla_eoq(evaluacion).to_excel(writer, sheet_name="EOQ sin restricciones", index=False)
        tabla_robustez(evaluacion).to_excel(writer, sheet_name="Robustez", index=False)
        tabla_cinco_escenarios(evaluacion, p).to_excel(writer, sheet_name="Capacidad", index=False)
        comparativa.to_excel(writer, sheet_name="Comparativa", index=False)
    return salida.getvalue()


# -----------------------------------------------------------------------------
# 5. Gráficas (Plotly)
# -----------------------------------------------------------------------------

def estilo_figura(fig, alto):
    fig.update_layout(
        template="plotly_white",
        height=alto,
        separators=",.",  # coma decimal, punto de miles
        font=dict(color=COLOR_TEXTO, size=13),
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


def serie_diente_sierra(Q, D, unidades_por_posicion):
    """Vértices del inventario (en posiciones) durante un año, en días.
    La tasa de demanda diaria es D / 365: cada ciclo dura Q / (D/365) días.
    """
    tasa = D / DIAS_ANIO
    ciclo = Q / tasa
    xs, ys = [], []
    inicio = 0.0
    while inicio < DIAS_ANIO:
        fin = min(inicio + ciclo, DIAS_ANIO)
        xs += [inicio, fin, None]
        # max(0, ...) evita valores como -0,0000001 por redondeo al final del ciclo.
        ys += [Q / unidades_por_posicion, max(0.0, Q - tasa * (fin - inicio)) / unidades_por_posicion, None]
        inicio += ciclo
    # Las líneas verticales de cada reposición.
    xs_rep, ys_rep = [], []
    inicio = ciclo
    while inicio < DIAS_ANIO:
        xs_rep += [inicio, inicio, None]
        ys_rep += [0, Q / unidades_por_posicion, None]
        inicio += ciclo
    return xs + xs_rep, ys + ys_rep


def grafica_diente_sierra(evaluacion, p, modo, base_eoq):
    """Diente de sierra en posiciones para EOQ de referencia, 20', 40' y proveedor local."""
    D = evaluacion["var"]["D"]
    u = p["und_posicion"]
    res = evaluacion["resultados"]

    # El EOQ de referencia se evalúa como una política más (mismo costo de pedido de su contenedor).
    base = res[base_eoq]
    referencia = evaluar_alternativa(
        "EOQ de referencia", base["EOQ"], base["EOQ"], base["A"], base["v"], evaluacion["var"], p, modo
    )
    paneles = [
        (f"EOQ de referencia (costos {base_eoq})", referencia, COLORES["EOQ de referencia"]),
        (ALT_20, res[ALT_20], COLORES[ALT_20]),
        (ALT_40, res[ALT_40], COLORES[ALT_40]),
        (f"{ALT_LOCAL} (Q = EOQ)", res[ALT_LOCAL], COLORES[ALT_LOCAL]),
    ]

    # Mismo eje Y en los cuatro paneles para comparar alturas de forma honesta.
    y_max = max(max(r["Q"] / u, r["capacidad_disponible"], p["pos_actual"]) for _, r, _ in paneles) * 1.15

    fig = make_subplots(rows=2, cols=2, subplot_titles=[t for t, _, _ in paneles],
                        vertical_spacing=0.16, horizontal_spacing=0.08)
    for i, (titulo, r, color) in enumerate(paneles):
        fila, col = i // 2 + 1, i % 2 + 1
        xs, ys = serie_diente_sierra(r["Q"], D, u)
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", line=dict(color=color, width=2), name=titulo, showlegend=False,
            hovertemplate="Día %{x:.0f}<br>%{y:.1f} posiciones<extra>" + titulo + "</extra>",
        ), row=fila, col=col)

        # Capacidad de la bodega actual.
        fig.add_hline(y=p["pos_actual"], line=dict(color=COLOR_SECUNDARIO, width=1.5, dash="dash"),
                      annotation_text=f"Bodega actual: {p['pos_actual']}",
                      annotation_position="top left", annotation_font_color=COLOR_SECUNDARIO,
                      row=fila, col=col)
        # Capacidad con alquiler o ampliación, si la política la usa o la intentó usar.
        if r["capacidad_disponible"] != p["pos_actual"]:
            fig.add_hline(y=r["capacidad_disponible"], line=dict(color=COLOR_TEXTO, width=1.5, dash="dot"),
                          annotation_text=f"{r['opcion_capacidad']}: {r['capacidad_disponible']}",
                          annotation_position="top left", annotation_font_color=COLOR_TEXTO,
                          row=fila, col=col)
        # Máximo de la política (posiciones requeridas) con su estado de factibilidad.
        estado = "factible" if r["factible"] else "NO factible"
        fig.add_annotation(
            x=DIAS_ANIO, y=r["Q"] / u, xanchor="right", yanchor="bottom", showarrow=False,
            text=f"Máx. {r['posiciones']} pos. · {estado}",
            font=dict(color=COLOR_LIMITE if not r["factible"] else COLOR_TEXTO, size=12),
            row=fila, col=col,
        )
        fig.update_xaxes(range=[0, DIAS_ANIO], title_text="Días" if fila == 2 else None, row=fila, col=col)
        fig.update_yaxes(range=[0, y_max], title_text="Posiciones" if col == 1 else None, row=fila, col=col)

    return estilo_figura(fig, 680)


def grafica_trc(evaluacion, incluir_local):
    """Curva TRC(Q) con el EOQ y las cantidades de los contenedores marcadas."""
    var = evaluacion["var"]
    D, r = var["D"], var["r"]
    res = evaluacion["resultados"]
    q_max = max(res[ALT_40]["Q"], res[ALT_40]["EOQ"], res[ALT_20]["EOQ"]) * 1.6
    qs = np.linspace(q_max * 0.02, q_max, 400)

    curvas = [ALT_20, ALT_40] + ([ALT_LOCAL] if incluir_local else [])
    fig = go.Figure()
    for nombre in curvas:
        r_alt = res[nombre]
        A, v = r_alt["A"], r_alt["v"]
        color = COLORES[nombre]
        fig.add_trace(go.Scatter(
            x=qs, y=[trc(q, A, D, v, r) / 1e6 for q in qs], mode="lines",
            line=dict(color=color, width=2), name=f"TRC(Q) con costos {nombre}",
            hovertemplate="Q = %{x:,.0f}<br>TRC = $%{y:,.2f} M<extra>" + nombre + "</extra>",
        ))
        # Mínimo de la curva: EOQ.
        fig.add_trace(go.Scatter(
            x=[r_alt["EOQ"]], y=[r_alt["TRC_EOQ"] / 1e6], mode="markers+text",
            marker=dict(color=color, size=11, symbol="diamond", line=dict(color="white", width=2)),
            text=[f"EOQ {numero(r_alt['EOQ'])}"], textposition="bottom center",
            textfont=dict(color=COLOR_TEXTO), showlegend=False,
            hovertemplate="EOQ = %{x:,.1f}<br>TRC mínimo = $%{y:,.2f} M<extra>" + nombre + "</extra>",
        ))
        # Cantidad real del contenedor sobre su propia curva.
        if nombre in ALT_IMPORTADAS:
            penal = (r_alt["TRC"] - r_alt["TRC_EOQ"]) / r_alt["TRC_EOQ"]
            fig.add_trace(go.Scatter(
                x=[r_alt["Q"]], y=[r_alt["TRC"] / 1e6], mode="markers+text",
                marker=dict(color=color, size=12, symbol="circle", line=dict(color="white", width=2)),
                text=[f"{nombre}: Q = {numero(r_alt['Q'])} (+{porcentaje(penal)} TRC)"],
                textposition="top center", textfont=dict(color=COLOR_TEXTO), showlegend=False,
                hovertemplate="Q = %{x:,.0f}<br>TRC = $%{y:,.2f} M<extra>" + nombre + "</extra>",
            ))

    techo = max(max(res[a]["TRC"] for a in ALT_IMPORTADAS), max(res[a]["TRC_EOQ"] for a in curvas)) * 1.8
    fig.update_xaxes(title_text="Cantidad a pedir Q (unidades)", range=[0, q_max])
    fig.update_yaxes(title_text="TRC (millones de $/año)", range=[0, techo / 1e6])
    return estilo_figura(fig, 520)


def barrido_sensibilidad(p, modo, clave, desde, hasta, puntos=61):
    """Recalcula el Costo Total Anual de cada alternativa para un rango del parámetro elegido."""
    c = CATALOGO_POR_CLAVE[clave]
    valores = np.linspace(desde, hasta, puntos)
    filas = []
    for x in valores:
        x_modelo = x / 100 if c["tipo"] == "pct" else x
        if c["tipo"] == "int" and clave in ("D", "pos_actual", "cap_20", "cap_40"):
            x_modelo = round(x_modelo)
        evaluacion = evaluar_todo(dict(p, **{clave: x_modelo}), modo)
        fila = {"x": x}
        for nombre in ALTERNATIVAS:
            res = evaluacion["resultados"][nombre]
            fila[nombre] = res["costo_total"] if res["factible"] else None
        fila["Recomendada"] = evaluacion["recomendada"]["alternativa"] if evaluacion["recomendada"] else "Ninguna"
        filas.append(fila)
    return pd.DataFrame(filas)


def grafica_sensibilidad(df, clave, valor_actual):
    c = CATALOGO_POR_CLAVE[clave]
    sufijo = " %" if c["tipo"] == "pct" else ""
    fig = go.Figure()
    for nombre in ALTERNATIVAS:
        y = [None if v is None or pd.isna(v) else v / 1e6 for v in df[nombre]]
        etiqueta = nombre if any(v is not None for v in y) else f"{nombre} (no factible en todo el rango)"
        fig.add_trace(go.Scatter(
            x=df["x"], y=y, mode="lines", name=etiqueta, line=dict(color=COLORES[nombre], width=2),
            connectgaps=False,
            hovertemplate="%{x:,.1f}" + sufijo + "<br>Costo total = $%{y:,.2f} M<extra>" + nombre + "</extra>",
        ))
    fig.add_vline(x=valor_actual, line=dict(color=COLOR_SECUNDARIO, width=1.5, dash="dash"),
                  annotation_text="Valor actual", annotation_position="top",
                  annotation_font_color=COLOR_SECUNDARIO)
    fig.update_xaxes(title_text=nombre_parametro(clave), tickformat=",.0f" if c["tipo"] == "int" else ",.1f")
    fig.update_yaxes(title_text="Costo Total Anual (millones de $)", tickformat=",.0f")
    return estilo_figura(fig, 480)


# -----------------------------------------------------------------------------
# 6. Interfaz de Streamlit
# -----------------------------------------------------------------------------

def etiqueta_estado(res):
    if res["factible"]:
        return f":material/check_circle: Factible · {res['opcion_capacidad']}"
    return f":material/block: No factible · {res['motivo']}"


def barra_lateral():
    """Todos los parámetros del caso, agrupados y editables."""
    with st.sidebar:
        st.header("Parámetros del caso")
        st.caption("Valores iniciales: pestaña **G6** del Excel del taller. Cambia cualquiera y todo se recalcula.")
        st.button("Restablecer valores G6", on_click=restablecer_g6, width="stretch")

        st.selectbox(
            "Capacidad adicional de bodega",
            options=list(MODOS_CAPACIDAD), format_func=MODOS_CAPACIDAD.get, key="modo_capacidad",
            help="Fuente de capacidad que puede usar una alternativa que no cabe en la bodega actual. "
                 "En automático se compara alquiler contra ampliación y se toma la más barata que alcance.",
        )

        for grupo in GRUPOS:
            with st.expander(grupo, expanded=grupo != "Información no relevante"):
                for c in [c for c in CATALOGO if c["grupo"] == grupo]:
                    etiqueta = f"{c['etiqueta']} ({c['unidad']})"
                    if c["tipo"] == "pct":
                        st.number_input(etiqueta, min_value=0.0, max_value=100.0, step=0.5,
                                        format="%.1f", key=clave_estado(c["clave"]))
                    else:
                        minimo = 0 if c["clase"] in ("Costo de ordenar", "Costo asociado a capacidad",
                                                     "Costo asociado a capacidad (molde)",
                                                     "Información no relevante") else 1
                        if c["clave"] in ("pos_actual", "pos_alquiler", "pos_ampliacion"):
                            minimo = 0
                        paso = 1 if c["unidad"] in ("unidades/posición", "posiciones") else (
                            100 if "unidad" in c["unidad"] and "$" not in c["unidad"] else 1000)
                        st.number_input(etiqueta, min_value=minimo, step=paso, format="%d",
                                        key=clave_estado(c["clave"]))
                if grupo == "Demanda y almacenamiento":
                    r_total = sum(st.session_state[clave_estado(k)]
                                  for k in ("r_capital", "r_seguro", "r_deterioro", "r_manejo"))
                    st.caption(f"Tasa de almacenamiento r = **{numero(r_total, 1)} %** anual")

        with st.expander("Cargar datos desde el Excel del taller"):
            archivo = st.file_uploader("Datos_por_equipo_Taller_EOQ.xlsx", type=["xlsx"], key="archivo_excel")
            hojas = []
            if archivo is not None:
                try:
                    hojas = pd.ExcelFile(io.BytesIO(archivo.getvalue())).sheet_names
                except Exception as e:  # noqa: BLE001
                    st.error(f"No se pudo abrir el archivo: {e}")
            if hojas:
                equipos = [h for h in hojas if h.upper().startswith("G")] or hojas
                st.selectbox("Pestaña del equipo", equipos,
                             index=equipos.index("G6") if "G6" in equipos else 0, key="hoja_excel")
                st.button("Cargar valores de la pestaña", on_click=cargar_desde_excel, width="stretch")

        mensaje = st.session_state.pop("mensaje_excel", None)
        if mensaje:
            tipo, texto = mensaje
            {"ok": st.success, "aviso": st.warning, "error": st.error}[tipo](texto)


def resumen_superior(evaluacion):
    rec = evaluacion["recomendada"]
    if rec is None:
        st.error("Ninguna alternativa es físicamente factible con los parámetros actuales. "
                 "Revisa la capacidad de bodega o la fuente de capacidad adicional.")
    else:
        factibles = sorted([r for r in evaluacion["resultados"].values() if r["factible"]],
                           key=lambda r: r["costo_total"])
        texto = f"**Alternativa recomendada: {rec['alternativa']}** · Costo Total Anual {pesos(rec['costo_total'])}"
        if rec["costo_capacidad"] > 0:
            texto += f" (incluye {rec['opcion_capacidad'].lower()}: {pesos(rec['costo_capacidad'])}/año)"
        if len(factibles) > 1:
            segunda = factibles[1]
            ahorro = segunda["costo_total"] - rec["costo_total"]
            texto += (f". Ahorra {pesos(ahorro)} al año ({porcentaje(ahorro / segunda['costo_total'], 2)}) "
                      f"frente a {segunda['alternativa']}.")
        st.success(md(texto), icon=":material/verified:")

    columnas = st.columns(3)
    for col, nombre in zip(columnas, ALTERNATIVAS):
        res = evaluacion["resultados"][nombre]
        with col.container(border=True):
            st.markdown(f"**{nombre}**")
            st.metric("Costo Total Anual", pesos(res["costo_total"]), label_visibility="visible")
            st.caption(etiqueta_estado(res))


def pestana_datos(p, evaluacion):
    st.subheader("Etapa 1 — Clasificación de la información")
    st.dataframe(tabla_clasificacion(p), hide_index=True, width="stretch")
    st.subheader("Variables del modelo")
    st.caption("El costo de almacenar una unidad durante un año es v·r (no existe una variable h independiente).")
    st.dataframe(formatear_variables(tabla_variables(evaluacion["var"])), hide_index=True, width="stretch")


def pestana_eoq(evaluacion):
    st.subheader("Etapa 2 — EOQ sin restricciones (benchmark económico)")
    st.latex(r"Q^* = \sqrt{\frac{2AD}{vr}} \qquad TRC(Q) = A\frac{D}{Q} + vr\frac{Q}{2}")
    st.dataframe(formatear(tabla_eoq(evaluacion), FORMATO_EOQ), hide_index=True, width="stretch")

    st.subheader("Etapa 3 — Cantidades reales de importación y robustez del EOQ")
    robustez = tabla_robustez(evaluacion)
    st.dataframe(formatear(robustez, FORMATO_ROBUSTEZ), hide_index=True, width="stretch")
    lineas = []
    for _, fila in robustez.iterrows():
        lineas.append(
            f"- **{fila['Alternativa']}**: la cantidad real se aleja {porcentaje(abs(fila['%ΔQ']))} del EOQ "
            f"({'por debajo' if fila['%ΔQ'] < 0 else 'por encima'}), pero el TRC solo sube "
            f"{porcentaje(fila['Penalización TRC'], 2)} ({pesos(fila['ΔTRC'])} al año)."
        )
    st.markdown(md("\n".join(lineas)))
    st.caption("El TRC es plano alrededor de su mínimo: una diferencia grande en cantidad produce una "
               "diferencia pequeña en costo. La tabla muestra la penalización para cualquier Q = k·EOQ: "
               "½(k + 1/k) − 1.")
    st.dataframe(tabla_penalizacion_generica(), hide_index=True)


def pestana_capacidad(evaluacion, p):
    st.subheader("Etapa 4 — Restricción de almacenamiento")
    st.caption(f"Cada posición almacena {p['und_posicion']} unidades. Las posiciones se calculan sobre el "
               "inventario máximo, justo después de recibir una reposición. Esta tabla compara alquiler "
               "y ampliación sin importar la opción elegida en la barra lateral.")
    st.dataframe(formatear(tabla_cinco_escenarios(evaluacion, p), FORMATO_ESCENARIOS),
                 hide_index=True, width="stretch")


def pestana_comparativa(evaluacion, p, modo):
    st.subheader("Tabla comparativa de alternativas")
    st.caption(f"Capacidad adicional: **{MODOS_CAPACIDAD[modo]}**. "
               "TRC de inventarios = ordenar + almacenar (analiza el Q). "
               "Costo Total Anual = adquisición + ordenar + almacenar + capacidad + molde (elige la alternativa).")
    texto, _ = tabla_comparativa(evaluacion)
    st.dataframe(texto, hide_index=True, width="stretch", height=640)

    rec = evaluacion["recomendada"]
    no_factibles = [r for r in evaluacion["resultados"].values() if not r["factible"]]
    for r in no_factibles:
        if rec is not None and r["costo_total"] < rec["costo_total"]:
            st.warning(md(f"{r['alternativa']} tendría un costo menor ({pesos(r['costo_total'])}), pero no se puede "
                          f"recomendar porque no es físicamente factible: {r['motivo']}."),
                       icon=":material/warning:")

    st.download_button(
        "Descargar resultados en Excel",
        data=excel_resultados(p, evaluacion, modo),
        file_name="resultados_EOQ_G6.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def pestana_graficas(evaluacion, p, modo):
    st.subheader("A. Inventario tipo diente de sierra (posiciones de almacenamiento, 1 año)")
    base_eoq = st.radio("EOQ de referencia calculado con los costos de", ALT_IMPORTADAS, horizontal=True,
                        key="base_eoq")
    st.caption("Tasa de demanda = D / 365 unidades por día. La línea discontinua es la bodega actual; "
               "la punteada, la capacidad con alquiler o ampliación (cambia con la opción de la barra lateral).")
    st.plotly_chart(grafica_diente_sierra(evaluacion, p, modo, base_eoq), theme=None)

    st.subheader("B. Curva TRC vs. cantidad a pedir")
    incluir_local = st.checkbox("Incluir la curva del proveedor local", value=False, key="trc_local")
    st.plotly_chart(grafica_trc(evaluacion, incluir_local), theme=None)


def pestana_sensibilidad(evaluacion, p, modo):
    st.subheader("Puntos de equilibrio")
    mejor = evaluacion["mejor_importacion"]
    local = evaluacion["resultados"][ALT_LOCAL]
    if mejor is None:
        st.info("No hay ninguna alternativa de importación factible, así que no hay contra qué comparar "
                "al proveedor local.")
    else:
        objetivo = mejor["costo_total"]
        st.caption(md(f"Referencia: mejor importación factible = **{mejor['alternativa']}** con Costo Total Anual "
                      f"{pesos(objetivo)}. El proveedor local es competitivo si su costo total es igual o menor."))
        col1, col2 = st.columns(2)

        with col1.container(border=True):
            st.markdown("**1. Precio máximo competitivo del proveedor local**")
            v_max, local_eq = precio_maximo_local(p, modo, objetivo)
            if v_max is None:
                st.write("Ni con precio cero sería competitivo: el molde y la capacidad ya superan "
                         "el costo de la mejor importación.")
            else:
                st.metric("Costo unitario máximo", pesos(v_max, 0),
                          delta=f"{pesos(v_max - p['v_local'])} vs. precio actual {pesos(p['v_local'])}",
                          delta_color="off")
                if local_eq is not None and not local_eq["factible"]:
                    st.warning(f"A ese precio el proveedor local no sería factible: {local_eq['motivo']}.")
                if p["v_local"] <= v_max:
                    st.write("El precio actual ya es competitivo.")
                else:
                    st.write(f"El precio actual debe bajar {porcentaje((p['v_local'] - v_max) / p['v_local'], 2)} "
                             "para igualar a la mejor importación.")

        with col2.container(border=True):
            st.markdown("**2. Financiación mínima del molde**")
            p_min = financiacion_minima(p, modo, objetivo)
            if p_min is None:
                st.write("No hay costo de molde: la financiación no cambia nada.")
            elif p_min <= 0:
                st.metric("Financiación mínima", "0 %")
                st.write("El proveedor local ya es competitivo sin financiación del molde.")
            elif p_min <= 1:
                st.metric("Financiación mínima", porcentaje(p_min, 2),
                          delta=f"actual {porcentaje(p['p_molde'], 1)}", delta_color="off")
                st.write("Con un porcentaje igual o mayor, el proveedor local queda en igualdad o mejor.")
            else:
                st.metric("Financiación mínima", "No alcanza",
                          delta=f"se necesitaría {porcentaje(p_min, 1)}", delta_color="off")
                v_100, _ = precio_maximo_local(p, modo, objetivo, financiacion=1.0)
                exceso = local["costo_total"] - local["costo_molde"] - objetivo
                texto = (f"Aunque el proveedor financie el 100 % del molde, su costo total sigue "
                         f"{pesos(exceso)} por encima de la mejor importación.")
                if v_100 is not None:
                    texto += f" Con el molde 100 % financiado, el precio tendría que bajar a {pesos(v_100)}."
                st.write(md(texto))

    st.divider()
    st.subheader("Análisis de sensibilidad")
    st.caption("Los parámetros de la barra lateral ya recalculan todo al instante. Aquí se barre un rango "
               "de un parámetro para ver cuándo cambia la recomendación. Las alternativas no factibles no se dibujan.")
    col1, col2, col3 = st.columns([2, 1, 1])
    clave = col1.selectbox("Parámetro", PARAMETROS_SENSIBILIDAD, format_func=nombre_parametro, key="sens_clave")
    c = CATALOGO_POR_CLAVE[clave]
    actual = st.session_state[clave_estado(clave)]
    if c["tipo"] == "pct":
        desde_def, hasta_def = 0.0, min(100.0, max(actual * 2, 10.0))
    else:
        desde_def, hasta_def = float(round(actual * 0.7)), float(round(actual * 1.3))
    # Si cambia el parámetro, se reinicia el rango alrededor de su valor actual.
    if st.session_state.get("sens_rango_de") != (clave, actual):
        st.session_state["sens_rango_de"] = (clave, actual)
        st.session_state["sens_desde"] = desde_def
        st.session_state["sens_hasta"] = hasta_def
    desde = col2.number_input("Desde", key="sens_desde", min_value=0.0)
    hasta = col3.number_input("Hasta", key="sens_hasta", min_value=0.0)
    if hasta <= desde:
        st.error("El valor 'Hasta' debe ser mayor que 'Desde'.")
        return

    df = barrido_sensibilidad(p, modo, clave, desde, hasta)
    st.plotly_chart(grafica_sensibilidad(df, clave, actual), theme=None)

    # Puntos donde cambia la alternativa recomendada.
    cambios = []
    for anterior, siguiente in zip(df.itertuples(), df.iloc[1:].itertuples()):
        if anterior.Recomendada != siguiente.Recomendada:
            cambios.append(f"- Entre {numero(anterior.x, 1)} y {numero(siguiente.x, 1)}: pasa de "
                           f"**{anterior.Recomendada}** a **{siguiente.Recomendada}**.")
    if cambios:
        st.markdown("La recomendación cambia en este rango:\n" + "\n".join(cambios))
    else:
        st.markdown(f"En todo el rango la recomendación se mantiene: **{df['Recomendada'].iloc[0]}**.")


def pestana_preguntas(p, modo):
    st.subheader("Preguntas de gerencia — Equipo G6")
    st.caption("Cada variación compara el valor original contra el nuevo, con el resto de parámetros tal como "
               "están en la barra lateral. El botón aplica el cambio en toda la herramienta.")
    for i, pregunta in enumerate(PREGUNTAS_G6):
        clave = pregunta["clave"]
        c = CATALOGO_POR_CLAVE[clave]
        a_modelo = (lambda x: x / 100) if c["tipo"] == "pct" else (lambda x: x)
        antes = evaluar_todo(dict(p, **{clave: a_modelo(pregunta["antes"])}), modo)
        despues = evaluar_todo(dict(p, **{clave: a_modelo(pregunta["despues"])}), modo)

        with st.container(border=True):
            st.markdown(f"**{pregunta['titulo']}**")
            st.write(md(pregunta["texto"]))
            filas = []
            for nombre in ALTERNATIVAS:
                ra, rd = antes["resultados"][nombre], despues["resultados"][nombre]
                filas.append({
                    "Alternativa": nombre,
                    "Costo total antes": pesos(ra["costo_total"]) + ("" if ra["factible"] else " (no factible)"),
                    "Costo total después": pesos(rd["costo_total"]) + ("" if rd["factible"] else " (no factible)"),
                    "Variación": pesos(rd["costo_total"] - ra["costo_total"]),
                })
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

            rec_a, rec_d = antes["recomendada"], despues["recomendada"]
            nombre_a = rec_a["alternativa"] if rec_a else "Ninguna"
            nombre_d = rec_d["alternativa"] if rec_d else "Ninguna"
            factibles_d = sorted([r for r in despues["resultados"].values() if r["factible"]],
                                 key=lambda r: r["costo_total"])
            margen = ""
            if len(factibles_d) > 1:
                margen = (f" La diferencia con la siguiente opción ({factibles_d[1]['alternativa']}) es de "
                          f"{pesos(factibles_d[1]['costo_total'] - factibles_d[0]['costo_total'])} al año.")
            if nombre_a != nombre_d:
                st.warning(md(f"**Sí cambia:** pasa de {nombre_a} a {nombre_d}.{margen}"), icon=":material/swap_horiz:")
            else:
                st.info(md(f"**No cambia:** se mantiene {nombre_d}.{margen}"), icon=":material/check:")

            b1, b2, _ = st.columns([1, 1, 2])
            b1.button(f"Aplicar {c['etiqueta'].lower()} = {numero(pregunta['despues'])}",
                      on_click=fijar_parametro, args=(clave, pregunta["despues"]), key=f"aplicar_{i}")
            b2.button(f"Volver a {numero(pregunta['antes'])}",
                      on_click=fijar_parametro, args=(clave, pregunta["antes"]), key=f"volver_{i}")


def main():
    st.set_page_config(page_title="Simulador EOQ G6", layout="wide")
    iniciar_estado()
    barra_lateral()

    st.title("Simulador EOQ: importación vs. proveedor local")
    st.caption("Equipo G6 · Taller evaluativo de Gestión de Inventarios · "
               "EOQ bajo restricciones logísticas y alternativas de abastecimiento")

    p = leer_parametros()
    modo = st.session_state["modo_capacidad"]
    var = calcular_variables(p)
    if var["r"] <= 0:
        st.error("La tasa de almacenamiento r debe ser mayor que 0 %. Revisa sus componentes en la barra lateral.")
        return
    if var["AL"] <= 0 or var["A20"] <= 0 or var["A40"] <= 0:
        st.error("Los costos de ordenar (A20, A40 y ALocal) deben ser mayores que 0.")
        return

    evaluacion = evaluar_todo(p, modo)
    resumen_superior(evaluacion)

    tabs = st.tabs([
        "1. Datos y variables",
        "2. EOQ y robustez",
        "3. Capacidad de bodega",
        "4. Comparativa",
        "5. Gráficas",
        "6. Sensibilidad y equilibrio",
        "7. Preguntas de gerencia",
    ])
    with tabs[0]:
        pestana_datos(p, evaluacion)
    with tabs[1]:
        pestana_eoq(evaluacion)
    with tabs[2]:
        pestana_capacidad(evaluacion, p)
    with tabs[3]:
        pestana_comparativa(evaluacion, p, modo)
    with tabs[4]:
        pestana_graficas(evaluacion, p, modo)
    with tabs[5]:
        pestana_sensibilidad(evaluacion, p, modo)
    with tabs[6]:
        pestana_preguntas(p, modo)


if __name__ == "__main__":
    main()
