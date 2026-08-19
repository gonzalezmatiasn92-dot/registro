import streamlit as st
import re
from logica import guardar_movimiento, calcular_arqueo_fisico, calcular_solo_cambio_chico, obtener_fecha_argentina

def evaluar_celda_excel(valor_texto):
    """Simula una celda de Excel resolviendo operaciones si inician con '='"""
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

def renderizar_cierre_caja(supabase_client, efectivo_caja_acumulado, movimientos_hoy):
    st.header("📋 Panel de Cierre de Caja y Arqueo General (Fin del Día)")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    tot_aran_hoy = sum(float(m.get("aranceles") or 0) for m in movimientos_hoy)
    tot_sell_hoy = sum(float(m.get("sellados") or 0) for m in movimientos_hoy)
    tot_pate_hoy = sum(float(m.get("patentes") or 0) for m in movimientos_hoy)
    tot_debi_hoy = sum(float(m.get("debito") or 0) for m in movimientos_hoy)
    
    with col1:
        st.markdown("#### 📑 1. Validar Totales Diarios")
        v_aran = st.number_input("Total Aranceles según planilla manual:", min_value=0.0, value=None, key="v_aran")
        if v_aran is not None:
            if round(v_aran, 2) == round(tot_aran_hoy, 2):
                st.success(f"✅ Coincide (${tot_aran_hoy:,.2f})")
            else:
                st.error(f"❌ Diferencia: ${round(v_aran - tot_aran_hoy, 2):,.2f}")
                
        v_sell = st.number_input("Total Sellados según planilla manual:", min_value=0.0, value=None, key="v_sell")
        if v_sell is not None:
            if round(v_sell, 2) == round(tot_sell_hoy, 2):
                st.success(f"✅ Coincide (${tot_sell_hoy:,.2f})")
            else:
                st.error(f"❌ Diferencia: ${round(v_sell - tot_sell_hoy, 2):,.2f}")
                
        v_pate = st.number_input("Total Patentes según planilla manual:", min_value=0.0, value=None, key="v_pate")
        if v_pate is not None:
            if round(v_pate, 2) == round(tot_pate_hoy, 2):
                st.success(f"✅ Coincide (${tot_pate_hoy:,.2f})")
            else:
                st.error(f"❌ Diferencia: ${round(v_pate - tot_pate_hoy, 2):,.2f}")

        st.markdown("---")
        st.markdown("#### 💳 Validación de Posnet")
        v_debi = st.number_input("Monto total según ticket de cierre de Posnet:", min_value=0.0, value=None, key="v_debi")
        if v_debi is not None:
            if round(v_debi, 2) == round(tot_debi_hoy, 2):
                st.success(f"✅ POSNET CUADRADO (${tot_debi_hoy:,.2f})")
            else:
                st.error(f"❌ Diferencia Posnet: ${round(v_debi - tot_debi_hoy, 2):,.2f} (Sistema: ${tot_debi_hoy:,.2f})")

        st.markdown("---")
        st.markdown("#### 🏦 Depositar en Banco (Retiro Físico)")
        t_monto_banco = st.text_input("Monto exacto retirado para enviar al banco ($):", placeholder="Ej: 50000 o =45000+5000", key="monto_banco")
        monto_banco = evaluar_celda_excel(t_monto_banco)
        
        if monto_banco > 0:
            st.info(f"💡 Valor procesado para depósito: ${monto_banco:,.2f}")
        
        if st.button("Confirmar Depósito Bancario", use_container_width=True, type="secondary"):
            if monto_banco and monto_banco > 0:
                usuario_actual = st.session_state.get("usuario_activo", "Sistema").strip()
                
                datos_retiro = {
                    "detalle": f"Depósito en Banco (Retiro parcial/total de Efectivo Acumulado)",
                    "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, 
                    "gastos": monto_banco, 
                    "efectivo": 0.0, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, 
                    "total_neto": float(-monto_banco),
                    "operador": usuario_actual
                }
                exito, msj = guardar_movimiento(supabase_client, datos_retiro)
                if exito:
                    st.success(f"💰 Depósito de ${monto_banco:,.2f} registrado por `{usuario_actual}`. El acumulado bajó.")
                    st.rerun()
                else:
                    st.error(msj)
            else:
                st.warning("Ingrese un monto superior a 0 para registrar el depósito.")
    with col2:
        st.markdown("#### 💵 2. Arqueo de Billetes Físico")
        
        st.markdown("""
            <div style="background-color: rgba(255, 140, 0, 0.08); padding: 6px 12px; border-radius: 6px; border-left: 4px solid rgba(255, 140, 0, 0.7); margin-bottom: 12px;">
                <span style="color: #c45a00; font-size: 13px; font-weight: bold;">🏦 Pendiente de deposito</span>
            </div>
        """, unsafe_allow_html=True)
        
        b20k = st.number_input("Billetes de $20.000 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b20k")
        b10k = st.number_input("Billetes de $10.000 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b10k")
        
        t_cambio_chico_dep = st.text_input("Cambio chico a Efectivo pendiente de depósito ($):", placeholder="", key="cc_dep")
        cambio_chico_dep = evaluar_celda_excel(t_cambio_chico_dep)
        
        st.markdown("""
            <div style="background-color: rgba(100, 220, 100, 0.08); padding: 6px 12px; border-radius: 6px; border-left: 4px solid rgba(100, 220, 100, 0.7); margin-top: 12px; margin-bottom: 12px;">
                <span style="color: #1e7d1e; font-size: 13px; font-weight: bold;">💵 Cambio de mañana</span>
            </div>
        """, unsafe_allow_html=True)
        
        b2k = st.number_input("Billetes de $2.000 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b2k")
        b1k = st.number_input("Billetes de $1.000 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b1k")
        b500 = st.number_input("Billetes de $500 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b500")
        b200 = st.number_input("Billetes de $200 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b200")
        b100 = st.number_input("Billetes de $100 (Cantidad):", min_value=0, step=1, value=None, placeholder="", key="b100")
        
    efectivo_real_contado = calcular_arqueo_fisico(b20k, b10k, b2k, b1k, b500, b200, b100)
    
    # El fajo que se aparta físicamente hoy para el sobre incluye billetes grandes y el cambio chico extra retirado
    monto_fajo_banco_hoy = float(((b20k or 0) * 20000) + ((b10k or 0) * 10000) + cambio_chico_dep)

    with col3:
        st.markdown("#### 📊 3. Auditoría de Caja Física Actual")
        
        # LÓGICA CORREGIDA: Cambio de mañana es estrictamente lo que quedó en el cajón chico (Total contado menos lo apartado para el sobre)
        cambio_de_manana = max(0.0, efectivo_real_contado - monto_fajo_banco_hoy)
        
        # CUENTAS SEPARADAS: El pozo permanente para el banco se calcula limpio sobre el acumulado histórico,
        # descontando el cambio fijo operativo del cajón para que no se mezclen los tantos.
        efectivo_pendiente_deposito = max(0.0, efectivo_caja_acumulado - cambio_de_manana)
        
        st.write("")
        st.metric(label="Efectivo en Caja Total (Esperado Histórico)", value=f"${efectivo_caja_acumulado:,.2f}")
        st.metric(label="Efectivo Contado en Cajón (Real Físico)", value=f"${efectivo_real_contado:,.2f}")
        
        st.markdown("---")
        
        st.markdown(f"""
            <div style="background-color: rgba(255, 140, 0, 0.12); border-left: 5px solid rgba(255, 140, 0, 0.7); padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                <span style="color: #444; font-size: 14px; font-weight: bold; display: block;">🏦 Pendiente de deposito</span>
                <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 4px;">${efectivo_pendiente_deposito:,.2f}</span>
            </div>
            
            <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgba(100, 220, 100, 0.7); padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                <span style="color: #444; font-size: 14px; font-weight: bold; display: block;">💵 Cambio de mañana</span>
                <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 4px;">${cambio_de_manana:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        auditoria_dif = round(efectivo_real_contado - efectivo_caja_acumulado, 2)
        if auditoria_dif == 0:
            st.success("✅ AUDITORÍA COMPLETA: Caja cuadrada.")
        elif auditoria_dif > 0:
            st.info(f" 🟩 SOBRANTE ACTUAL: ${auditoria_dif:,.2f}")
        else:
            st.error(f" 🟥 FALTANTE ACTUAL: ${abs(auditoria_dif):,.2f}")
            
        st.write("")
        if st.button("🔒 Ejecutar Cierre y Traspasar Cambio", type="primary", use_container_width=True):
            usuario_cierre = st.session_state.get("usuario_activo", "Sistema")
            
            if cambio_de_manana > 0:
                datos_apertura = {
                    "detalle": "Apertura de Caja: Fondo de Cambio del día anterior",
                    "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": 0.0,
                    "efectivo": cambio_de_manana, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, 
                    "total_neto": float(cambio_de_manana),
                    "operador": usuario_cierre
                }
                guardar_movimiento(supabase_client, datos_apertura)
                
            st.success("🔒 Caja guardada con éxito. El cambio fue traspasado de manera independiente.")
            st.rerun()
