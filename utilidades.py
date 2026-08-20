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
    
    # Inyectamos estilos CSS para que las letras sean más grandes y todo esté bien agrupado
    st.html("""
        <style>
        .st-emotion-cache-16idsys p { font-size: 18px !important; margin: 0 !important; }
        .form-label-big { font-size: 19px !important; font-weight: bold !important; color: #111111; }
        .pedido-azul { background-color: rgba(0, 123, 255, 0.15); border-left: 4px solid #007bff; padding: 2px 8px; border-radius: 4px; font-weight: bold; color: #0056b3; font-size: 18px; }
        .pedido-ok { color: #888888; font-size: 18px; }
        </style>
    """)
    
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
                estado_tramite = "🟢 TRÁMITE SALDADO"
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

    # 📑 SECCIÓN 2: Control de Stock de Formularios (CAJITA COMPACTA SOLICITADA)
    with st.expander("📋 2. Control de Stock de Formularios", expanded=True):
        # Diccionario maestro con los valores ideales solicitados
        ideales_formularios = {
            "02": 10, "04": 20, "08": 30, "08D": 35, "TP": 90, "57": 5, "59": 5, "HojCONT": 150
        }
        
        # Encabezado ultra corto de las 4 columnas básicas
        c_st, c_stock, c_ideal, c_pedido = st.columns(4)
        c_st.markdown("**📄 ST**")
        c_stock.markdown("**🔢 STOCK**")
        c_ideal.markdown("**📋 DEBERÍA**")
        c_pedido.markdown("**🚨 PEDIDO**")
        st.markdown("---")
        
        # Renderizado en casilleros pequeños sin desperdicio de espacio
        for form, ideal_val in ideales_formularios.items():
            col_st, col_stock, col_ideal, col_pedido = st.columns(4)
            
            # 1. Columna ST: Solo el nombre corto
            col_st.markdown(f"<span class='form-label-big'>{form}</span>", unsafe_allow_html=True)
            
            # 2. Columna STOCK: Casillero numérico miniatura agrupado
            stock_ingresado = col_stock.number_input(
                label=f"stk_{form}", 
                min_value=0, 
                step=1, 
                value=0, 
                label_visibility="collapsed", 
                key=f"mini_stk_{form}"
            )
            
            # 3. Columna DEBERÍA TENER (Ideal fijo)
            col_ideal.markdown(f"<span style='font-size: 18px;'>{ideal_val} u.</span>", unsafe_allow_html=True)
            
            # 4. Columna PEDIDO AUTOMÁTICO: Si falta stock, se pinta la celda de AZUL
            falta_unidades = max(0, ideal_val - stock_ingresado)
            if falta_unidades > 0:
                col_pedido.markdown(f"<div class='pedido-azul'>Pedir {falta_unidades} u.</div>", unsafe_allow_html=True)
            else:
                col_pedido.markdown("<div class='pedido-ok'>0</div>", unsafe_allow_html=True)
