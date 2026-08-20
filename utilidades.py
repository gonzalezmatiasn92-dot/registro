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
    
    with St.expander("📝 1. Calculadora de Saldos de Trámite y Generador de E-mails", expanded=True):
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
                    <div style="background-color: rgba(255, 75, 75, 0.15); border-left: 5px solid rgb(255, 75, 75); padding: 15px; border-radius: 6px;">
                        <span style="color: #ff4b4b; font-size: 15px; font-weight: bold; display: block;">🟥 TOTAL A DEPOSITAR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${abs(diferencia_final):,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"FALTA DEPOSITAR: ${abs(diferencia_final):,.2f} LOS COSTOS SUPERAN EL DEPOSITO INICIAL"
                color_borde_html = "#FF4D4F"
            elif diferencia_final == 0:
                st.markdown("""
                    <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgb(40, 167, 69); padding: 15px; border-radius: 6px;">
                        <span style="color: #28a745; font-size: 15px; font-weight: bold; display: block;">🟩 TRÁMITE SALDADO</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">$0.00</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = "TRÁMITE SALDADO"
                color_borde_html = "#52C41A"
            else:
                st.markdown(f"""
                    <div style="background-color: rgba(0, 123, 255, 0.12); border-left: 5px solid rgb(0, 123, 255); padding: 15px; border-radius: 6px;">
                        <span style="color: #007bff; font-size: 15px; font-weight: bold; display: block;">🟦 TOTAL A SU FAVOR</span>
                        <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 5px;">${diferencia_final:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                estado_tramite = f"TOTAL A SU FAVOR: ${diferencia_final:,.2f}"
                color_borde_html = "#1890FF"

        st.markdown("---")
        st.markdown("##### ✉ Rendición Formateada (Simulación Excel)")
        st.write("Presione el botón azul de abajo. Al pegarlo en Gmail, se insertará como celdas de Excel perfectas:")
        
        # Confeccionamos la tabla HTML con bordes de celda idénticos a los que exporta Excel
        html_copiar = f"""<div style="font-family: Arial, sans-serif; font-size: 14px; color: #000000;">
<p style="margin-bottom: 15px; font-weight: bold;">PATENTE: {patente if patente else '_______'}</p>
<table style="border-collapse: collapse; width: 320px; font-size: 14px; border: 1px solid #D9D9D9;">
    <tr>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; background-color: #FAFAFA;">Deposito</td>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; text-align: right; font-weight: bold;">${deposito:,.2f}</td>
    </tr>
    <tr>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px;">Arancel</td>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; text-align: right;">${arancel:,.2f}</td>
    </tr>
    <tr>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px;">Sellado de prenda</td>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; text-align: right;">${prenda:,.2f}</td>
    </tr>
    <tr>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px;">Sellado</td>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; text-align: right;">${sell_alta:,.2f}</td>
    </tr>
    <tr>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px;">Alta</td>
        <td style="border: 1px solid #D9D9D9; padding: 6px 10px; text-align: right;">${alta:,.2f}</td>
    </tr>
</table>
<br>
<table style="border-collapse: collapse; width: 440px; font-size: 14px; font-weight: bold; border: 2px solid {color_borde_html};">
    <tr>
        <td style="padding: 12px 15px; background-color: #FAFAFA; text-align: center; color: #000000;">{estado_tramite}</td>
    </tr>
</table>
</div>"""

        # Mostramos una vista previa visual en la pantalla de cómo va a lucir en Gmail
        st.markdown(html_copiar, unsafe_allow_html=True)
        st.write("")
        
        # El botón ejecuta una inyección de JavaScript que escribe tanto texto plano como HTML enriquecido en el portapapeles
        if st.button("📋 Copiar Celdas de Excel para Gmail", use_container_width=True, type="primary"):
            st.html(f"""
                <script>
                const htmlType = "text/html";
                const plainType = "text/plain";
                const blobHtml = new Blob([`{html_copiar}`], {{ type: htmlType }});
                const blobPlain = new Blob([`PATENTE: {patente}\\n\\nDeposito: ${deposito}\\nArancel: ${arancel}\\n{estado_tramite}`], {{ type: plainType }});
                const data = [new ClipboardItem({{ [htmlType]: blobHtml, [plainType]: blobPlain }})];
                navigator.clipboard.write(data);
                </script>
            """)
            st.success("✅ ¡Celdas copiadas con formato Excel! Ya podés ir a Gmail y presionar Ctrl+V (Pegar).")
