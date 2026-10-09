# =============================================================================
# Verificación del simulador EOQ contra cálculos manuales (sección 15 del taller)
# -----------------------------------------------------------------------------
# Valida la app por etapas, en el mismo orden en que se construyó:
#   1. Funciones del modelo (variables, EOQ, TRC)
#   2. Restricción de capacidad
#   3. Escenarios (cantidades reales, cinco posibilidades de bodega)
#   4. Tabla comparativa y alternativa recomendada
#   5. Interfaz (la app corre completa sin errores)
#   6. Visualizaciones (diente de sierra y curva TRC)
#   7. Sensibilidad, puntos de equilibrio y preguntas de gerencia
#
# Los valores esperados se calculan aquí "a mano" con aritmética directa
# (sin usar las funciones de app.py) y se comparan con lo que calcula la app.
# Los de las etapas 1 a 4 coinciden con los resultados del Excel del equipo G6.
#
# Uso:  python verificar_modelo.py        -> todas las etapas
#       python verificar_modelo.py 1 2    -> solo las etapas indicadas
# =============================================================================

import math
import re
import sys

import app

fallas = 0


def revisar(descripcion, obtenido, esperado, tolerancia=1e-6):
    """Compara un valor de la app contra el esperado y muestra el resultado."""
    global fallas
    if isinstance(esperado, (int, float)) and not isinstance(esperado, bool):
        ok = obtenido is not None and abs(obtenido - esperado) <= tolerancia * max(1.0, abs(esperado))
    else:
        ok = obtenido == esperado
    if not ok:
        fallas += 1
    print(f"  [{'OK' if ok else 'FALLA'}] {descripcion}: app = {obtenido!r} | esperado = {esperado!r}")


# Parámetros G6 en unidades del modelo (los porcentajes como fracción).
P = {c["clave"]: (c["valor"] / 100 if c["tipo"] == "pct" else c["valor"]) for c in app.CATALOGO}

# --- Cálculo manual de referencia (datos de la pestaña G6) ---
D = 11500
r = 0.20 + 0.02 + 0.05 + 0.03                 # 0,30
A20 = 7130000 + 2200000 + 3000000 + 700000   # 13.030.000
A40 = 8640000 + 2500000 + 4000000 + 700000   # 15.840.000
AL = 360000 + 155000 + 103000                # 618.000
V_IMP, V_LOCAL = 98500, 107000


def etapa_1():
    print("Etapa 1 — Funciones del modelo (variables, EOQ, TRC)")
    var = app.calcular_variables(P)
    revisar("D", var["D"], D)
    revisar("A20", var["A20"], A20)
    revisar("A40", var["A40"], A40)
    revisar("ALocal", var["AL"], AL)
    revisar("r", var["r"], r)
    revisar("v·r importado", var["v_imp"] * var["r"], 29550)
    revisar("v·r local", var["v_local"] * var["r"], 32100)

    # EOQ y TRC(Q*) contra los resultados del Excel del equipo (filas 50 a 52).
    excel = {
        "20'": (A20, V_IMP, 3184.6182770027503, 94105470.08543128),
        "40'": (A40, V_IMP, 3511.2581805034333, 103757679.23387648),
        "local": (AL, V_LOCAL, 665.4349993183083, 21360463.4781177),
    }
    for nombre, (A, v, q_excel, trc_excel) in excel.items():
        q = app.eoq(A, D, v, r)
        revisar(f"EOQ {nombre}", q, q_excel)
        revisar(f"TRC(Q*) {nombre}", app.trc(q, A, D, v, r), trc_excel)
        # En el EOQ, costo de ordenar = costo de almacenar.
        revisar(f"ordenar = almacenar en Q* {nombre}", A * D / q, v * r * q / 2)


def etapa_2():
    print("Etapa 2 — Restricción de capacidad")
    revisar("posiciones 20' (1900/25)", app.posiciones_requeridas(1900, 25), 76)
    revisar("posiciones 40' (4200/25)", app.posiciones_requeridas(4200, 25), 168)
    revisar("posiciones local (665,4/25)", app.posiciones_requeridas(665.4349993183083, 25), 27)
    revisar("posiciones exactas no suben (50/25)", app.posiciones_requeridas(50, 25), 2)

    cap = app.evaluar_capacidad(76, P, "auto")
    revisar("20' no cabe en 65 → ampliación (más barata)", cap["opcion"], "Ampliación")
    revisar("costo capacidad 20'", cap["costo"], 10500000)
    revisar("capacidad con ampliación", cap["capacidad"], 65 + 90)
    revisar("20' con solo alquiler cuesta 20 M", app.evaluar_capacidad(76, P, "alquiler")["costo"], 20000000)
    revisar("20' con solo bodega actual no cabe", app.evaluar_capacidad(76, P, "actual")["cabe"], False)
    revisar("40' (168) no cabe ni con 155", app.evaluar_capacidad(168, P, "auto")["cabe"], False)
    revisar("40' combinando ambas (245) sí cabe", app.evaluar_capacidad(168, P, "ambas")["cabe"], True)
    revisar("costo 40' combinando ambas", app.evaluar_capacidad(168, P, "ambas")["costo"], 30500000)
    revisar("20' en modo combinado sigue usando solo ampliación",
            app.evaluar_capacidad(76, P, "ambas")["costo"], 10500000)
    revisar("local (27) cabe en bodega actual", app.evaluar_capacidad(27, P, "auto")["costo"], 0.0)


def etapa_3():
    print("Etapa 3 — Escenarios: cantidades reales y cinco posibilidades de bodega")
    ev = app.evaluar_todo(P, "auto")
    rob = app.tabla_robustez(ev).set_index("Alternativa")
    # Contra el Excel del equipo (filas 56 y 57).
    revisar("ΔQ 20'", rob.loc["Contenedor 20'", "ΔQ (unidades)"], -1284.6182770027503)
    revisar("%ΔQ 20'", rob.loc["Contenedor 20'", "%ΔQ"], -0.4033821843827975)
    revisar("TRC(1900)", rob.loc["Contenedor 20'", "TRC(Q contenedor)"], 106938289.4736842)
    revisar("penalización 20'", rob.loc["Contenedor 20'", "Penalización TRC"], 0.1363663491251144)
    revisar("%ΔQ 40'", rob.loc["Contenedor 40'", "%ΔQ"], 0.19615242858553256)
    revisar("TRC(4200)", rob.loc["Contenedor 40'", "TRC(Q contenedor)"], 105426428.57142858)
    revisar("penalización 40'", rob.loc["Contenedor 40'", "Penalización TRC"], 0.01608314054317495)
    # Fórmula general de penalización: ½(k + 1/k) − 1 con k = Q/EOQ.
    k = 1900 / 3184.6182770027503
    revisar("penalización 20' con ½(k+1/k)−1", 0.5 * (k + 1 / k) - 1, 0.1363663491251144)

    esc = app.tabla_cinco_escenarios(ev, P)
    revisar("son cinco escenarios", len(esc), 5)
    revisar("20' + bodega actual: no cabe", esc.iloc[0]["¿Cabe?"], "No")
    revisar("20' + alquiler/ampliación: cabe", esc.iloc[1]["¿Cabe?"], "Sí")
    revisar("20' + alquiler/ampliación: costo", esc.iloc[1]["Costo anual de capacidad"], 10500000)
    revisar("40' + bodega actual: no cabe", esc.iloc[2]["¿Cabe?"], "No")
    revisar("40' + alquiler/ampliación: no cabe", esc.iloc[3]["¿Cabe?"], "No")
    revisar("proveedor local: cabe", esc.iloc[4]["¿Cabe?"], "Sí")


def etapa_4():
    print("Etapa 4 — Tabla comparativa y alternativa recomendada")
    ev = app.evaluar_todo(P, "auto")
    res = ev["resultados"]
    total_20 = V_IMP * D + A20 * D / 1900 + V_IMP * r * 1900 / 2 + 10500000
    total_40 = V_IMP * D + A40 * D / 4200 + V_IMP * r * 4200 / 2
    total_local = 1287860463.4781177  # fila 78 del Excel del equipo
    revisar("costo total 20' (con ampliación)", res["Contenedor 20'"]["costo_total"], total_20)
    revisar("costo total 20' ≈ 1.250.188.289", round(total_20), 1250188289)
    revisar("costo total 40' (sin capacidad, no factible)", res["Contenedor 40'"]["costo_total"], total_40)
    revisar("40' no factible", res["Contenedor 40'"]["factible"], False)
    revisar("costo total local (Excel)", res["Proveedor local"]["costo_total"], total_local)
    revisar("molde empresa = 45 M × 80 %", res["Proveedor local"]["costo_molde"], 36000000)
    revisar("recomendada", ev["recomendada"]["alternativa"], "Contenedor 20'")
    revisar("mejor importación", ev["mejor_importacion"]["alternativa"], "Contenedor 20'")
    # El 40' es más barato que el 20' pero no se puede recomendar (no cabe).
    revisar("40' sería más barato que 20'", total_40 < total_20, True)

    texto, numerico = app.tabla_comparativa(ev)
    revisar("filas de la comparativa", len(texto), 17)
    revisar("columnas de la comparativa", list(texto.columns), ["Indicador"] + app.ALTERNATIVAS)

    ev_ambas = app.evaluar_todo(P, "ambas")
    revisar("modo combinado: 40' factible con 30,5 M",
            ev_ambas["resultados"]["Contenedor 40'"]["costo_total"], total_40 + 30500000)
    revisar("modo combinado: sigue recomendada 20'", ev_ambas["recomendada"]["alternativa"], "Contenedor 20'")

    ev_actual = app.evaluar_todo(P, "actual")
    revisar("solo bodega actual: recomendada local", ev_actual["recomendada"]["alternativa"], "Proveedor local")


def etapa_5():
    print("Etapa 5 — Interfaz (la app corre completa sin errores)")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("app.py", default_timeout=60).run()
    revisar("sin excepciones", len(at.exception), 0)
    revisar("siete pestañas", len(at.tabs), 7)
    revisar("mensaje de recomendación", "Contenedor 20'" in at.success[0].value, True)

    # Un $ sin escapar en un texto markdown se vuelve fórmula LaTeX y daña el texto.
    textos = [e.value for grupo in (at.success, at.warning, at.info, at.markdown, at.caption) for e in grupo]
    sin_escapar = [t for t in textos if re.search(r"(?<!\\)\$", t)]
    revisar("textos con $ sin escapar", sin_escapar, [])

    # Cambiar un parámetro desde la barra lateral recalcula la recomendación (Variación 1).
    at.number_input(key="par_v_local").set_value(102000).run()
    revisar("sin excepciones tras cambiar v local", len(at.exception), 0)
    revisar("con v local = 102.000 recomienda local", "Proveedor local" in at.success[0].value, True)

    # El botón de restablecer (barra lateral) vuelve a los valores G6.
    at.sidebar.button[0].click().run()
    revisar("restablecer vuelve a 107.000", at.number_input(key="par_v_local").value, 107000)

    # Los botones de las preguntas de gerencia aplican el cambio en toda la herramienta.
    at.button(key="aplicar_2").click().run()
    revisar("aplicar V3 fija el flete 20' en 10.000.000", at.number_input(key="par_flete_20").value, 10000000)
    revisar("con V3 se mantiene contenedor 20'", "Contenedor 20'" in at.success[0].value, True)
    at.button(key="volver_2").click().run()
    revisar("volver deja el flete en 7.130.000", at.number_input(key="par_flete_20").value, 7130000)

    # Solo bodega actual: el 20' deja de ser factible.
    at.selectbox(key="modo_capacidad").set_value("actual").run()
    revisar("solo bodega actual recomienda local", "Proveedor local" in at.success[0].value, True)


def etapa_6():
    print("Etapa 6 — Visualizaciones")
    ev = app.evaluar_todo(P, "auto")
    # Diente de sierra del 20': ciclo = 1900 / (11500/365) días y pico = 76 posiciones.
    xs, ys = app.serie_diente_sierra(1900, D, 25)
    ciclo = 1900 / (D / 365)
    revisar("ciclo 20' (días)", ev["resultados"]["Contenedor 20'"]["ciclo_dias"], ciclo)
    revisar("pico 20' en posiciones", max(y for y in ys if y is not None), 76)
    revisar("mínimo 20' en posiciones", min(y for y in ys if y is not None), 0)
    revisar("eje x llega a 365 días", max(x for x in xs if x is not None), 365)
    # Cada reposición aparece dos veces (inicio del diente y línea vertical): se cuentan los días distintos.
    reposiciones = len({round(x, 6) for x, y in zip(xs, ys) if y == 76 and x not in (None, 0)})
    revisar("reposiciones dentro del año 20'", reposiciones, math.floor(365 / ciclo))

    fig = app.grafica_diente_sierra(ev, P, "auto", "Contenedor 20'")
    lineas = [s.y0 for s in fig.layout.shapes]
    revisar("hay línea de bodega actual (65)", 65 in lineas, True)
    revisar("hay línea de capacidad con ampliación (155)", 155 in lineas, True)
    fig_alq = app.grafica_diente_sierra(app.evaluar_todo(P, "alquiler"), P, "alquiler", "Contenedor 20'")
    revisar("la línea se actualiza con alquiler",
            any("Alquiler" in (a.text or "") for a in fig_alq.layout.annotations), True)

    fig_trc = app.grafica_trc(ev, incluir_local=False)
    puntos = [(t.x[0], t.y[0]) for t in fig_trc.data if t.mode == "markers+text"]
    revisar("curva TRC marca EOQ y contenedores (4 puntos)", len(puntos), 4)
    revisar("punto 20' en TRC(1900) (millones)", (1900, 106938289.4736842 / 1e6) in
            [(round(x), round(y, 6)) for x, y in puntos] or
            any(abs(x - 1900) < 1e-9 and abs(y - 106.9382894736842) < 1e-6 for x, y in puntos), True)


def etapa_7():
    print("Etapa 7 — Sensibilidad, puntos de equilibrio y preguntas de gerencia")
    ev = app.evaluar_todo(P, "auto")
    objetivo = ev["mejor_importacion"]["costo_total"]

    # Precio máximo del proveedor local, resuelto por bisección (método distinto al de la app).
    def total_local(v):
        return v * D + math.sqrt(2 * AL * D * v * r) + 45000000 * 0.8

    bajo, alto = 1.0, 200000.0
    for _ in range(200):
        medio = (bajo + alto) / 2
        bajo, alto = (medio, alto) if total_local(medio) < objetivo else (bajo, medio)
    v_max, _ = app.precio_maximo_local(P, "auto", objetivo)
    revisar("precio máximo local (bisección)", v_max, bajo)
    print(f"      → precio máximo competitivo ≈ ${v_max:,.0f}")

    # Financiación mínima: 1 − (objetivo − costo local sin molde) / molde.
    p_min = app.financiacion_minima(P, "auto", objetivo)
    p_manual = 1 - (objetivo - (1287860463.4781177 - 36000000)) / 45000000
    revisar("financiación mínima del molde", p_min, p_manual)
    revisar("no alcanza ni con 100 %", p_min > 1, True)
    print(f"      → se necesitaría financiar {p_min:.2%} del molde")

    # Sensibilidad: el barrido en el valor actual coincide con la evaluación normal.
    df = app.barrido_sensibilidad(P, "auto", "v_local", 107000, 107000 * 1.3, puntos=5)
    revisar("barrido en el valor actual = costo local", df.iloc[0]["Proveedor local"],
            ev["resultados"]["Proveedor local"]["costo_total"])
    df = app.barrido_sensibilidad(P, "auto", "v_local", 95000, 110000, puntos=31)
    revisar("barrido de v local cambia la recomendación", df["Recomendada"].nunique(), 2)

    # Preguntas de gerencia G6, recalculadas a mano.
    def total_local_con(v):
        return v * D + math.sqrt(2 * AL * D * v * r) + 36000000

    ev1 = app.evaluar_todo(dict(P, v_local=102000), "auto")
    revisar("V1: costo local con $102.000", ev1["resultados"]["Proveedor local"]["costo_total"], total_local_con(102000))
    revisar("V1: cambia a proveedor local", ev1["recomendada"]["alternativa"], "Proveedor local")

    total_20_v2 = 105000 * D + A20 * D / 1900 + 105000 * r * 1900 / 2 + 10500000
    ev2 = app.evaluar_todo(dict(P, v_imp=105000), "auto")
    revisar("V2: costo 20' con arancel", ev2["resultados"]["Contenedor 20'"]["costo_total"], total_20_v2)
    revisar("V2: cambia a proveedor local", ev2["recomendada"]["alternativa"], "Proveedor local")

    A20_v3 = 10000000 + 2200000 + 3000000 + 700000
    total_20_v3 = V_IMP * D + A20_v3 * D / 1900 + V_IMP * r * 1900 / 2 + 10500000
    ev3 = app.evaluar_todo(dict(P, flete_20=10000000), "auto")
    revisar("V3: costo 20' con flete $10 M", ev3["resultados"]["Contenedor 20'"]["costo_total"], total_20_v3)
    revisar("V3: se mantiene contenedor 20'", ev3["recomendada"]["alternativa"], "Contenedor 20'")


ETAPAS = {1: etapa_1, 2: etapa_2, 3: etapa_3, 4: etapa_4, 5: etapa_5, 6: etapa_6, 7: etapa_7}

if __name__ == "__main__":
    elegidas = [int(a) for a in sys.argv[1:]] or list(ETAPAS)
    for n in elegidas:
        ETAPAS[n]()
        print()
    print("Todo coincide con los cálculos manuales." if fallas == 0 else f"{fallas} verificación(es) fallaron.")
    sys.exit(1 if fallas else 0)
