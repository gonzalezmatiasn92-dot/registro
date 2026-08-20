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
    
    with st.expander("📝 1. Calculadora de Saldos de Trámite y Generador de E-mails", expanded=True):
        st.write("Complete los campos para calcular las diferencias de depósitos y confeccionar el e-mail automático.")
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
                    <div style="background-color: rgba(255, 140, 0, 0.12); border-left: 5px solid rgb(255, 75, 75); padding: 15px; border-radius: 6px;">
                        <span style="color: #ff4b4b; font-size: 15px; font-weight: bold; display: block;">🟥 TOTAL A DEPOSITAR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${abs(diferencia_final):,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Bloque visual de color para el e-mail (Falta dinero)
                bloque_veredicto_render = f"""
                <div style="background-color: #FFF5F5; border: 2px solid #CC3333; padding: 14px; border-radius: 6px; text-align: center; margin-top: 15px; max-width: 440px;">
                    <b style="color: #CC3333; font-size: 16px;">🟥 FALTA DEPOSITAR: ${abs(diferencia_final):,.2f}</b><br>
                    <span style="color: #555555; font-size: 12px; display: block; margin-top: 3px;">Los costos superan el depósito inicial.</span>
                </div>"""
                
            elif diferencia_final == 0:
                st.markdown("""
                    <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgb(40, 167, 69); padding: 15px; border-radius: 6px;">
                        <span style="color: #28a745; font-size: 15px; font-weight: bold; display: block;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">$0.00</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Bloque visual de color para el e-mail (Justo)
                bloque_veredicto_render = """
                <div style="background-color: #F6FFED; border: 2px solid #389E0D; padding: 14px; border-radius: 6px; text-align: center; margin-top: 15px; max-width: 440px;">
                    <b style="color: #389E0D; font-size: 16px;">🟩 TRÁMITE SALDADO</b>
                </div>"""
            else:
                st.markdown(f"""
                    <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgb(0, 123, 255); padding: 15px; border-radius: 6px;">
                        <span style="color: #007bff; font-size: 15px; font-weight: bold; display: block;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${diferencia_final:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Bloque visual de color para el e-mail (A favor)
                bloque_veredicto_render = f"""
                <div style="background-color: #E6F7FF; border: 2px solid #1890FF; padding: 14px; border-radius: 6px; text-align: center; margin-top: 15px; max-width: 440px;">
                    <b style="color: #1890FF; font-size: 16px;">🟦 TOTAL A SU FAVOR: ${diferencia_final:,.2f}</b>
                </div>"""

        st.markdown("---")
        st.markdown("##### ✉ E-mail Confeccionado Visualmente (Seleccione con el mouse para copiar)")
        st.write("Pinte el texto de abajo con el cursor del mouse, haga clic derecho, seleccione 'Copiar' y péguelo directo en Gmail:")
        
        # CORREGIDO: Renderizado visual en texto enriquecido mediante HTML directo. El cajero copia la imagen visual y el formato viaja intacto.
        st.markdown(f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #111111; max-width: 450px; padding: 12px; border: 1px dashed #BBBBBB; border-radius: 6px; background-color: #FAFAFA;">
            <div style="background-color: #F0F2F5; padding: 8px 12px; border-radius: 4px; font-weight: bold; font-size: 15px; margin-bottom: 12px;">
                PATENTE: {patente if patente else '_______'}
            </div>
            
            <p style="margin: 4px 0;"><b>Deposito:</b> ${deposito:,.2f}</p>
            <p style="margin: 4px 0;"><b>Arancel:</b> ${arancel:,.2f}</p>
            <p style="margin: 4px 0;"><b>Sellado de prenda:</b> ${prenda:,.2f}</p>
            <p style="margin: 4px 0;"><b>Sellado:</b> ${sell_alta:,.2f}</p>
            <p style="margin: 4px 0;"><b>Alta:</b> ${alta:,.2f}</p>
            
            {bloque_veredicto_render}
        </div>
        """, unsafe_allow_html=True)
