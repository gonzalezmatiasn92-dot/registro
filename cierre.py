import streamlit as st
from logica import guardar_movimiento, calcular_arqueo_fisico, calcular_solo_cambio_chico

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

    with col2:
        st.markdown("#### 💵 2. Arqueo de Billetes Físico")
        b20k = st.number_input("Billetes de $20.000 (Cantidad):", min_value=0, step=1, value=None, key="b20k")
        b10k = st.number_input("Billetes de $10.000 (Cantidad):", min_value=0, step=1, value=None, key="b10k")
        b2k = st.number_input("Billetes de $2.000 (Cantidad):", min_value=0, step=1, value=None, key="b2k")
        b1k = st.number_input("Billetes de $1.000 (Cantidad):", min_value=0, step=1, value=None, key="b1k")
        b500 = st.number_input("Billetes de $500 (Cantidad):", min_value=0, step=1, value=None, key="b500")
        b200 = st.number_input("Billetes de $200 (Cantidad):", min_value=0, step=1, value=None, key="b200")
        b100 = st.number_input("Billetes de $100 (Cantidad):", min_value=0, step=1, value=None, key="b100")
        
    efectivo_real_contado = calcular_arqueo_fisico(b20k, b10k, b2k, b1k, b500, b200, b100)
    cambio_chico_calculado = calcular_solo_cambio_chico(b2k, b1k, b500, b200, b100)

    with col3:
        st.markdown("#### 📊 3. Retención de Cambio")
        monto_cambio_retener = st.number_input("Suma que queda en cambio para mañana ($):", min_value=0.0, value=float(cambio_chico_calculado), key="cambio_retener")
        propuesta_banco = max(0.0, efectivo_real_contado - monto_cambio_retener)
        
        st.markdown("---")
        st.markdown("#### 🏦 Cierre Final Basado en Auditoría")
        st.metric(label="Efectivo en Caja (Esperado)", value=f"${efectivo_caja_acumulado:,.2f}")
        st.metric(label="Efectivo Contado (Real)", value=f"${efectivo_real_contado:,.2f}")
        st.metric(label="Efectivo a enviar al Banco", value=f"${propuesta_banco:,.2f}")
        
        auditoria_dif = round(efectivo_real_contado - efectivo_caja_acumulado, 2)
        if auditoria_dif == 0:
            st.success("✅ AUDITORÍA COMPLETA: Caja cuadrada.")
        elif auditoria_dif > 0:
            st.info(f" 🟩 SOBRANTE: ${auditoria_dif:,.2f}")
        else:
            st.error(f" 🟥 FALTANTE: ${abs(auditoria_dif):,.2f}")
            
        if st.button("🔒 Ejecutar Cierre y Traspasar Cambio", type="primary", use_container_width=True):
            datos_retiro = {
                "detalle": f"Depósito Bancario - Cierre de Caja (Arqueo Real: ${efectivo_real_contado:,.2f})",
                "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": propuesta_banco,
                "efectivo": 0.0, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, "total_neto": float(-propuesta_banco)
            }
            exito_ret, msj_ret = guardar_movimiento(supabase_client, datos_retiro)
            
            if exito_ret:
                if monto_cambio_retener > 0:
                    datos_apertura = {
                        "detalle": "Apertura de Caja: Fondo de Cambio del día anterior",
                        "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": 0.0,
                        "efectivo": monto_cambio_retener, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0, "total_neto": float(monto_cambio_retener)
                    }
                    guardar_movimiento(supabase_client, datos_apertura)
                st.success("Cierre de caja procesado con éxito.")
                st.rerun()
            else:
                st.error(msj_ret)
