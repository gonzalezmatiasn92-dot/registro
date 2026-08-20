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
        
        # Estructuramos la pantalla en dos columnas principales para mejor equilibrio visual
        col_izquierda, col_derecha = st.columns([1.8, 2], gap="large")
        
        with col_izquierda:
            st.markdown("#### 📥 Valores de Entrada")
            
            # Contenedor visual estilizado para los campos de datos
            with st.container(border=True):
                patente = st.text_input("NÚMERO DE PATENTE:", placeholder="Ej: AI424NJ").strip().upper()
                st.markdown("---")
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
            
        # Operaciones matemáticas del Excel
        saldo_despues_arancel = deposito - arancel
        saldo_despues_prenda = saldo_despues_arancel - prenda
        saldo_despues_sell_alta = saldo_despues_prenda - sell_alta
        diferencia_final = saldo_despues_sell_alta - alta
        
        with col_derecha:
            st.markdown("#### 📊 Control y Descuentos Parciales")
            
            # Contenedor visual con la cascada de descuentos alineada y limpia
            with st.container(border=True):
                c_desc, c_val = st.columns([1.5, 1])
                
                c_desc.write("• Saldo inicial post Arancel:")
                c_val.markdown(f"**${saldo_despues_arancel:,.2f}**")
                
                c_desc.write("• Saldo post Sellado Prenda:")
                c_val.markdown(f"**${saldo_despues_prenda:,.2f}**")
                
                c_desc.write("• Saldo post Sellado Alta:")
                c_val.markdown(f"**${saldo_despues_sell_alta:,.2f}**")
                
                st.markdown("---")
                c_desc.write("🔹 **Diferencia Final Neta:**")
                c_val.markdown(f"**${diferencia_final:,.2f}**")

            st.write("")
            
            # MARQUESINA DE VERDICTO DE GRANDES DIMENSIONES
            if diferencia_final < 0:
                st.markdown(f"""
                    <div style="background-color: rgba(255, 75, 75, 0.1); border: 2px solid rgb(255, 75, 75); padding: 18px; border-radius: 8px; text-align: center;">
                        <span style="color: #ff4b4b; font-size: 16px; font-weight: bold; display: block; letter-spacing: 0.5px;">🟥 TOTAL A DEPOSITAR</span>
                        <span style="color: black; font-size: 32px; font-weight: 800; display: block; margin-top: 6px;">${abs(diferencia_final):,.2f}</span>
                        <span style="color: #555; font-size: 13px; display: block; margin-top: 4px;">Los costos superaron el depósito inicial.</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"FALTA DEPOSITAR: ${abs(diferencia_final):,.2f} debido a que los costos superaron el depósito inicial"
            elif diferencia_final == 0:
                st.markdown("""
                    <div style="background-color: rgba(40, 167, 69, 0.1); border: 2px solid rgb(40, 167, 69); padding: 18px; border-radius: 8px; text-align: center;">
                        <span style="color: #28a745; font-size: 16px; font-weight: bold; display: block; letter-spacing: 0.5px;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 32px; font-weight: 800; display: block; margin-top: 6px;">$0.00</span>
                        <span style="color: #555; font-size: 13px; display: block; margin-top: 4px;">El saldo cubre los costos de forma exacta.</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = "TRÁMITE SALDADO"
            else:
                st.markdown(f"""
                    <div style="background-color: rgba(0, 123, 255, 0.08); border: 2px solid rgb(0, 123, 255); padding: 18px; border-radius: 8px; text-align: center;">
                        <span style="color: #007bff; font-size: 16px; font-weight: bold; display: block; letter-spacing: 0.5px;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 32px; font-weight: 800; display: block; margin-top: 6px;">${diferencia_final:,.2f}</span>
                        <span style="color: #555; font-size: 13px; display: block; margin-top: 4px;">El cliente posee crédito disponible.</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"TOTAL A SU FAVOR: ${diferencia_final:,.2f}"

        st.markdown("---")
        st.markdown("#### ✉ Generador de Texto para Gmail")
        st.write("Haga clic en el botón de copiar (ícono de hojas empalmadas arriba a la derecha del cuadro) para llevarlo listo a Gmail:")
        
        cuerpo_email = f"""PATENTE: {patente if patente else '_______'}

Deposito: ${deposito:,.2f}
Arancel: ${arancel:,.2f}
Sellado de prenda: ${prenda:,.2f}
Sellado: ${sell_alta:,.2f}
Alta: ${alta:,.2f}

--------------------------------------------------
{estado_tramite.upper()}
--------------------------------------------------
"""
        st.code(cuerpo_email, language="text", wrap_lines=True)
