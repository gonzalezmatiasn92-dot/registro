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
    
    # Usamos un expansor oculto para que no ocupe espacio visual si no se está usando
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
            
        # LÓGICA DE DESCUENTOS PARCIALES IDÉNTICA A TU EXCEL
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
            
            # SEMÁFORO INTELIGENTE SEGÚN EL SALDO FINAL
            if diferencia_final < 0:
                # Falta plata: Cartel Rojo de 'Total a depositar'
                st.markdown(f"""
                    <div style="background-color: rgba(255, 100, 100, 0.15); border-left: 5px solid rgb(255, 75, 75); padding: 15px; border-radius: 6px;">
                        <span style="color: #ff4b4b; font-size: 15px; font-weight: bold; display: block;">🟥 TOTAL A DEPOSITAR</span>
                        <span style="color: black; font-size: 26px; font-weight: bold; display: block; margin-top: 5px;">${abs(diferencia_final):,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"Falta depositar un total de ${abs(diferencia_final):,.2f} debido a que los costos superaron el depósito inicial."
            elif diferencia_final == 0:
                # Cero: Cartel Verde de Coincidencia exacta
                st.markdown("""
                    <div style="background-color: rgba(100, 220, 100, 0.15); border-left: 5px solid rgb(40, 167, 69); padding: 15px; border-radius: 6px;">
                        <span style="color: #28a745; font-size: 15px; font-weight: bold; display: block;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 26px; font-weight: bold; display: block; margin-top: 5px;">$0.00</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = "El depósito cubrió de forma exacta el total de los costos del trámite."
            else:
                # Le sobra plata: Cartel Azul de 'Total a su favor'
                st.markdown(f"""
                    <div style="background-color: rgba(0, 191, 255, 0.12); border-left: 5px solid rgb(0, 123, 255); padding: 15px; border-radius: 6px;">
                        <span style="color: #007bff; font-size: 15px; font-weight: bold; display: block;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 26px; font-weight: bold; display: block; margin-top: 5px;">${diferencia_final:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"Queda un saldo a su favor de ${diferencia_final:,.2f} disponible en caja."

        st.markdown("---")
        st.markdown("##### ✉ Generador de E-mail Profesional (Listo para copiar)")
        
        # Confección del texto del Mail estructurado de forma automática
        cuerpo_email = f"""Asunto: Detalle de Saldos y Rendición de Trámite - Patente {patente if patente else '_______'}

Estimado cliente,

Le acercamos el desglose correspondiente a la liquidación del trámite de la patente {patente if patente else '_______'}:

• Depósito Inicial: ${deposito:,.2f}
--------------------------------------------------
• Costo de Arancel: ${arancel:,.2f}
• Sellado Prenda: ${prenda:,.2f}
• Sellado Alta: ${sell_alta:,.2f}
• Alta: ${alta:,.2f}
--------------------------------------------------

Resultado del Balance:
{estado_tramite}

Ante cualquier consulta, quedamos a su entera disposición.

Atentamente,
Administración de Mostrador
"""
        
        st.text_area("Texto confeccionado para Gmail:", value=cuerpo_email, height=350, key="txt_area_mail")
        
        # Botón nativo moderno para copiar el e-mail al portapapeles con un clic
        st.copy_to_clipboard(cuerpo_email, before_copy_label="📋 Copiar E-mail completo", after_copy_label="✅ ¡Copiado en el portapapeles!")
