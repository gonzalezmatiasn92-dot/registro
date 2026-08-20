import streamlit as st
import re

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
                color_texto_final = "#CC3333"
            elif diferencia_final == 0:
                st.markdown("""
                    <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgb(40, 167, 69); padding: 15px; border-radius: 6px;">
                        <span style="color: #28a745; font-size: 15px; font-weight: bold; display: block;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">$0.00</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = "🟩 TRÁMITE SALDADO"
                color_texto_final = "#28A745"
            else:
                st.markdown(f"""
                    <div style="background-color: rgba(0, 123, 255, 0.12); border-left: 5px solid rgb(0, 123, 255); padding: 15px; border-radius: 6px;">
                        <span style="color: #007bff; font-size: 15px; font-weight: bold; display: block;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${diferencia_final:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"🔵 TOTAL A SU FAVOR: ${diferencia_final:,.2f}"
                color_texto_final = "#007BFF"

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

    # 📑 SECCIÓN 2: Control de Stock de Formularios
    with st.expander("📋 2. Control y Planificación de Stock de Formularios", expanded=True):
        st.write("Ingrese el stock físico disponible actual en el mostrador para calcular el pedido automático necesario.")
        st.write("")
        
        # Diccionario fijo con las bases ideales operativas solicitadas
        ideales_formularios = {
            "02": 10, "04": 20, "08": 30, "08D": 35, "TP": 90, "57": 5, "59": 5, "HojCONT": 150
        }
        
        # Diseñamos los títulos de las 4 columnas de forma simétrica
        c_st, c_stock, c_ideal, c_pedido = st.columns(4)
        
        c_st.markdown("**📄 ST**")
        c_stock.markdown("**🔢 STOCK ACTUAL**")
        c_ideal.markdown("**📋 DEBERÍA TENER**")
        c_pedido.markdown("**🚨 PEDIDO AUTOMÁTICO**")
        st.markdown("---")
        
        # Iteramos renglón por renglón el stock de cada formulario de forma prolija
        for form_name, cant_ideal in ideales_formularios.items():
            col_st, col_stock, col_ideal, col_pedido = st.columns(4)
            
            # Columna 1: Nombre del Formulario fijo
            col_st.write("")
            col_st.markdown(f"**Formulario {form_name}**")
            
            # Columna 2: Casillero libre para ingresar el Stock Físico real
            stock_real = col_stock.number_input(
                label=f"Stock {form_name}", 
                min_value=0, 
                step=1, 
                value=0, 
                label_visibility="collapsed", 
                key=f"stk_{form_name}"
            )
            
            # Columna 4: Muestra el stock ideal fijo que debés tener en el mostrador
            col_ideal.write("")
            col_ideal.write(f"{cant_ideal} unidades")
            
            # Columna 3: Calcula cuántos hay que pedir de forma automática
            falta_pedir = max(0, cant_ideal - stock_real)
            col_pedido.write("")
            if falta_pedir > 0:
                # Si falta stock, te lo resalta con un texto en negrita indicando la compra requerida
                col_pedido.markdown(f"<span style='color: #ff4b4b; font-weight: bold;'> pedir {falta_pedir} u.</span>", unsafe_allow_html=True)
            else:
                # Si estás cubierto, te estampa un ok sutil que no ensucia la pantalla
                col_pedido.markdown("<span style='color: #28a745;'>✅ Stock OK</span>", unsafe_allow_html=True)
