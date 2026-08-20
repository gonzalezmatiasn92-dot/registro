import streamlit as st
import re
import pandas as pd

def evaluar_celda_excel(valor_texto):
    """Permite resolver operaciones matemáticas básicas si inician con '=' como en Excel"""
    if not valor_texto:
        return 0.0
    texto_limpio = str(valor_texto).strip().replace(" ", "")
    if not texto_limpio:
        return 0.0
    if texto_limpio.startswith("="):
        formula = texto_limpio[1:]
        if not re.match(r"^[0-9.+\-*/()]+$", formula):
            return 0.0
        try:
            return float(eval(formula))
        except Exception:
            return 0.0
    else:
        try:
            return float(texto_limpio.replace(",", "."))
        except ValueError:
            return 0.0

def renderizar_panel_utilidades():
    st.header("🧰 Panel de Utilidades y Asistente de Gestión")
    st.markdown("---")
    
    # 📝 SECCIÓN 1: Calculadora de Saldos de Trámite
    with st.expander("📝 1. Calculadora de Saldos de Trámite y Generador de E-mails", expanded=False):
        st.write("Complete los campos para generar el texto de la rendición.")
        st.write("")
        
        col1, col2, col3 = st.columns([1.5, 1, 1.5])
        
        with col1:
            st.markdown("##### 📥 Valores de Entrada")
            patente = st.text_input("NÚMERO DE PATENTE:", placeholder="Ej: AI424NJ").strip().upper()
            
            t_deposito = st.text_input("Depósito Inicial ($):", placeholder="Ej: 1700000", key="ut_dep")
            t_arancel = st.text_input("Arancel ($):", placeholder="Ej: 525370", key="ut_aran")
            t_prenda = st.text_input("Sellado Prenda ($):", placeholder="Ej: 0", key="ut_pren")
            t_sell_alta = st.text_input("Sellado Alta ($):", placeholder="Ej: 1287500", key="ut_salta")
            t_alta = st.text_input("Alta ($):", placeholder="Ej: 125887.10", key="ut_alta")
            
            deposito = evaluar_celda_excel(t_deposito)
            arancel = evaluar_celda_excel(t_arancel)
            prenda = evaluar_celda_excel(t_prenda)
            sell_alta = evaluar_celda_excel(t_sell_alta)
            alta = evaluar_celda_excel(t_alta)
            
        saldo_despues_arancel = deposito - arancel
        saldo_despues_prenda = saldo_despues_arancel - prenda
        saldo_despues_sell_alta = saldo_despues_prenda - sell_alta
        diferencia_final = saldo_despues_sell_alta - alta
        
        with col2:
            st.markdown("##### 📉 Descuento Parcial")
            st.write("")
            st.write("")
            st.write("")
            st.write(f"**Saldo:** ${saldo_despues_arancel:,.2f}")
            st.write("")
            st.write(f"**Saldo:** ${saldo_despues_prenda:,.2f}")
            st.write("")
            st.write(f"**Saldo:** ${saldo_despues_sell_alta:,.2f}")
            st.write("")
            st.write(f"**Diferencia:** ${diferencia_final:,.2f}")
            
        with col3:
            st.markdown("##### 🚦 Veredicto y Balance")
            st.write("")
            st.write("")
            
            if diferencia_final < 0:
                st.markdown(f"""
                    <div style="background-color: rgba(255, 75, 75, 0.15); border-left: 5px solid rgb(255, 75, 75); padding: 15px; border-radius: 6px;">
                        <span style="color: #ff4b4b; font-size: 15px; font-weight: bold; display: block;">🟥 TOTAL A DEPOSITAR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${abs(diferencia_final):,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"🔴 FALTA DEPOSITAR: ${abs(diferencia_final):,.2f} LOS COSTOS SUPERAN EL DEPOSITO INICIAL"
            elif diferencia_final == 0:
                st.markdown("""
                    <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgb(40, 167, 69); padding: 15px; border-radius: 6px;">
                        <span style="color: #28a745; font-size: 15px; font-weight: bold; display: block;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">$0.00</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = "🟩 TRÁMITE SALDADO"
            else:
                st.markdown(f"""
                    <div style="background-color: rgba(0, 123, 255, 0.12); border-left: 5px solid rgb(0, 123, 255); padding: 15px; border-radius: 6px;">
                        <span style="color: #007bff; font-size: 15px; font-weight: bold; display: block;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${diferencia_final:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"🔵 TOTAL A SU FAVOR: ${diferencia_final:,.2f}"

        st.markdown("---")
        st.markdown("##### ✉ Texto Confeccionado para Gmail")
        st.write("Pinte el recuadro blanco de abajo arrastrando el mouse, cópielo (Ctrl+C) y péguelo en Gmail:")
        st.write("")
        
        st.markdown(f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #000000; max-width: 450px; padding: 10px; background-color: #FFFFFF;">
            <p style="margin: 0 0 10px 0; font-weight: bold;">PATENTE: {patente if patente else '_______'}</p>
            <table style="width: 100%; border: 0; border-collapse: collapse;">
                <tr><td style="width: 200px; padding: 2px 0;">Deposito:</td><td style="text-align: left; font-weight: bold;">${deposito:,.2f}</td></tr>
                <tr><td style="padding: 2px 0;">Arancel:</td><td style="text-align: left;">${arancel:,.2f}</td></tr>
                <tr><td style="padding: 2px 0;">Sellado de prenda:</td><td style="text-align: left;">${prenda:,.2f}</td></tr>
                <tr><td style="padding: 2px 0;">Sellado:</td><td style="text-align: left;">${sell_alta:,.2f}</td></tr>
                <tr><td style="padding: 2px 0;">Alta:</td><td style="text-align: left;">${alta:,.2f}</td></tr>
            </table>
            <p style="margin: 12px 0 0 0; font-weight: bold; color: #000000;">{estado_tramite}</p>
        </div>
        """, unsafe_allow_html=True)

    # 📑 SECCIÓN 2: Control de Stock de Formularios (REDISEÑADO COMPACTO)
    with st.expander("📋 2. Control y Planificación de Stock de Formularios", expanded=True):
        st.write("Haga doble clic en la celda de STOCK ACTUAL para escribir. El pedido y las alertas se calculan solos:")
        st.write("")

        # 🧠 Cargamos las variables ideales fijas en la sesión para que no se borren al refrescar
        ideales = {"02": 10, "04": 20, "08": 30, "08D": 35, "TP": 90, "57": 5, "59": 5, "HojCONT": 150}
        
        if "util_stock_data" not in st.session_state:
            st.session_state.util_stock_data = {f: 0 for f in ideales.keys()}

        # Construimos el DataFrame agrupado compacto para la mini grilla interactiva tipo Excel
        filas_tabla = []
        for form, ideal_val in ideales.items():
            stk_actual = st.session_state.util_stock_data[form]
            ped_automatico = max(0, ideal_val - stk_actual)
            
            filas_tabla.append({
                "ST": f"Formulario {form}",
                "STOCK ACTUAL": stk_actual,
                "DEBERÍA TENER": ideal_val,
                "PEDIDO AUTOMÁTICO": ped_automatico,
                "ALERTA GRÁFICA": ped_automatico # Esta columna alimenta la barra visual de Streamlit
            })
            
        df_stock = pd.DataFrame(filas_tabla)

        # 🖥️ RENDERIZADO ULTRA COMPACTO: Inyectamos st.data_editor con barras de progreso rojas
        grid_stock = st.data_editor(
            df_stock,
            use_container_width=True,
            hide_index=True,
            disabled=["ST", "DEBERÍA TENER", "PEDIDO AUTOMÁTICO"], # El cajero solo puede tocar la columna de Stock Actual
            column_config={
                "ST": st.column_config.TextColumn("📄 ST", help="Tipo de Formulario"),
                "STOCK ACTUAL": st.column_config.NumberColumn("🔢 STOCK ACTUAL", min_value=0, step=1),
                "DEBERÍA TENER": st.column_config.NumberColumn("📋 DEBERÍA TENER", format="%d u."),
                "PEDIDO AUTOMÁTICO": st.column_config.NumberColumn("🚨 PEDIDO", format=" pedir %d u."),
                # MODIFICADO VISUAL: Se introduce un gráfico de barras rojas que salta a la vista si falta mercadería
                "ALERTA GRÁFICA": st.column_config.ProgressColumn(
                    "📊 ESTADO CRÍTICO",
                    help="Barra llena indica urgencia de compra",
                    format="",
                    min_value=0,
                    max_value=150, # Tepeado al tope máximo de HojCONT
                    color="red"
                )
            },
            key="editor_stock_util"
        )

        # Sincronizador en caliente: Si el operador cambió un número de stock, recalculamos la grilla al instante
        if st.session_state.get("editor_stock_util") and "edited_rows" in st.session_state["editor_stock_util"]:
            cambios_grilla = st.session_state["editor_stock_util"]["edited_rows"]
            if cambios_grilla:
                for idx_fila, dict_cambios in cambios_grilla.items():
                    if "STOCK ACTUAL" in dict_cambios:
                        form_modificado = df_stock.iloc[idx_fila]["ST"].replace("Formulario ", "")
                        nuevo_valor = int(dict_cambios["STOCK ACTUAL"] or 0)
                        st.session_state.util_stock_data[form_modificado] = nuevo_valor
                st.rerun()
