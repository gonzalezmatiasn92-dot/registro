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
    
    usuario_activo = st.session_state.get("usuario_activo", "Sistema")
    fecha_hoy_str = obtener_fecha_argentina().strftime("%Y-%m-%d")

    # 🔐 VERIFICACIÓN DE CONTROL DE CIERRES: Chequeamos si hoy ya se cerró la caja operativa
    try:
        chequeo_cierre = supabase_client.table("movimientos").select("id").eq("detalle", "Apertura de Caja: Fondo de Cambio del día anterior").like("fecha_operacion", f"{fecha_hoy_str}%").execute()
        caja_cerrada_hoy = len(chequeo_cierre.data) > 0
    except Exception:
        caja_cerrada_hoy = False

    if caja_cerrada_hoy:
        st.error("🔒 La caja de la fecha ya fue cerrada de forma definitiva.")
        st.info("⚠️ El sistema ha bloqueado las operaciones del día de hoy. Mañana se volverá a habilitar de forma automática al cambiar de fecha.")
        return

    monto_fondo_inicial = 0.0
    try:
        apertura_reg = (
            supabase_client.table("movimientos")
            .select("efectivo")
            .ilike("detalle", "%Fondo de Cambio%")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        if apertura_reg.data and len(apertura_reg.data) > 0:
            monto_fondo_inicial = float(apertura_reg.data.get("efectivo") or 0.0)
    except Exception:
        pass
        
    col1, col2, col3 = st.columns(3)
    
    # CORREGIDO: Filtramos para que la planilla no compute la consolidación automática del fajo ni aperturas dentro de los totales diarios operativos
    movs_filtrados = [
        m for m in movimientos_hoy 
        if "Consolidación de Efectivo" not in str(m.get("detalle") or "") 
        and "Apertura de Caja" not in str(m.get("detalle") or "")
    ]
    
    tot_aran_hoy = sum(float(m.get("aranceles") or 0) for m in movs_filtrados)
    tot_sell_hoy = sum(float(m.get("sellados") or 0) for m in movs_filtrados)
    tot_pate_hoy = sum(float(m.get("patentes") or 0) for m in movs_filtrados)
    tot_debi_hoy = sum(float(m.get("debito") or 0) for m in movs_filtrados)
    
    # Calculamos el efectivo esperado de hoy depurando las inyecciones automáticas del cierre
    efectivo_esperado_hoy = sum(float(m.get("efectivo") or 0) - float(m.get("gastos") or 0) for m in movs_filtrados)
    
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
        st.markdown("#### 🏦 Depositar en Banco (Retiro Físico del Pozo)")
        t_monto_banco = st.text_input("Monto exacto retirado para enviar al banco ($):", placeholder="Ej: 50000 o =45000+5000", key="monto_banco")
        monto_banco = evaluar_celda_excel(t_monto_banco)
        
        if monto_banco > 0:
            st.info(f"💡 Valor procesado para depósito: ${monto_banco:,.2f}")
        
        if st.button("Confirmar Depósito Bancario", use_container_width=True, type="secondary"):
            if monto_banco and monto_banco > 0:
                datos_retiro = {
                    "detalle": f"Depósito en Banco (Retiro parcial/total de Efectivo Acumulado)",
                    "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, 
                    "gastos": monto_banco, 
                    "efectivo": 0.0, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, 
                    "total_neto": float(-monto_banco),
                    "operador": usuario_activo
                }
                exito, msj = guardar_movimiento(supabase_client, datos_retiro)
                if exito:
                    st.success(f"💰 Depósito de ${monto_banco:,.2f} registrado por `{usuario_activo}`. El pozo pendiente bajó.")
                    st.rerun()
                else:
                    st.error(msj)
            else:
                st.warning("Ingrese un monto superior a 0 para registrar el depósito.")
    with col2:
        st.markdown("#### 💵 2. Arqueo de Billetes Físico (Solo de Hoy)")
        
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
        
    efectivo_total_contado_hoy = float((b20k or 0)*20000 + (b10k or 0)*10000 + (b2k or 0)*2000 + (b1k or 0)*1000 + (b500 or 0)*500 + (b200 or 0)*200 + (b100 or 0)*100 + cambio_chico_dep)
    monto_fajo_banco_hoy = float(((b20k or 0) * 20000) + ((b10k or 0) * 10000) + cambio_chico_dep)
    cambio_de_manana_dinamico = float((b2k or 0)*2000 + (b1k or 0)*1000 + (b500 or 0)*500 + (b200 or 0)*200 + (b100 or 0)*100)

    with col3:
        st.markdown("#### 📊 3. Auditoría de Caja Física Actual")
        
        efectivo_total_esperado_con_cambio = efectivo_esperado_hoy + monto_fondo_inicial
        auditoria_dif = round(efectivo_total_contado_hoy - efectivo_total_esperado_con_cambio, 2)
        efectivo_pendiente_deposito_directo = efectivo_caja_acumulado + monto_fajo_banco_hoy

        st.write("")
        st.metric(label="Efectivo Esperado según Planilla (Solo Hoy)", value=f"${efectivo_esperado_hoy:,.2f}")
        st.metric(label="Efectivo Contado Real en Cajón (Solo Hoy)", value=f"${efectivo_total_contado_hoy:,.2f}")
        
        st.markdown("---")
        
        st.markdown(f"""
            <div style="background-color: rgba(255, 140, 0, 0.12); border-left: 5px solid rgba(255, 140, 0, 0.7); padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                <span style="color: #444; font-size: 14px; font-weight: bold; display: block;">🏦 Pendiente de deposito</span>
                <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 4px;">${efectivo_pendiente_deposito_directo:,.2f}</span>
            </div>
            
            <div style="background-color: rgba(100, 220, 100, 0.12); border-left: 5px solid rgba(100, 220, 100, 0.7); padding: 12px; border-radius: 6px; margin-bottom: 15px;">
                <span style="color: #444; font-size: 14px; font-weight: bold; display: block;">💵 Cambio de mañana</span>
                <span style="color: black; font-size: 24px; font-weight: bold; display: block; margin-top: 4px;">${cambio_de_manana_dinamico:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if auditoria_dif == 0:
            st.success("✅ AUDITORÍA DEL DÍA: Caja cuadrada perfecta.")
        elif auditoria_dif > 0:
            st.info(f" 🟩 SOBRANTE DE HOY: ${auditoria_dif:,.2f}")
        else:
            st.error(f" 🟥 FALTANTE DE HOY: ${abs(auditoria_dif):,.2f}")
            
        st.markdown("---")
        confirmado = st.checkbox("✔ Confirmar Cierre Diario", key="chk_conf_cierre")
        if confirmado:
            st.warning("⚠️ Advertencia: Al confirmar el cierre, la planilla diaria se bloqueará por completo por el resto del día.")
            
        st.write("")
        if st.button("🔒 Ejecutar Cierre y Traspasar Cambio", type="primary", use_container_width=True, disabled=not confirmado):
            if monto_fajo_banco_hoy > 0:
                datos_fajo = {
                    "detalle": "Consolidación de Efectivo: Fajo diario derivado al pozo pendiente de depósito",
                    "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": 0.0,
                    "efectivo": monto_fajo_banco_hoy, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, 
                    "total_neto": float(monto_fajo_banco_hoy),
                    "operador": usuario_cierre
                }
                guardar_movimiento(supabase_client, datos_fajo)

            if cambio_de_manana_dinamico > 0:
                datos_apertura = {
                    "detalle": "Apertura de Caja: Fondo de Cambio del día anterior",
                    "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": 0.0,
                    "efectivo": cambio_de_manana_dinamico, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, 
                    "total_neto": float(cambio_de_manana_dinamico),
                    "operador": usuario_cierre
                }
                guardar_movimiento(supabase_client, datos_apertura)
                
            st.success("🔒 Caja de hoy guardada con éxito. El fajo nuevo fue sumado al pozo de la nube.")
            st.rerun()
