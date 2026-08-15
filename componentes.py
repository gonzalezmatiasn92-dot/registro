import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logica

def inyectar_estilos():
    st.markdown("""
        <style>
        div[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        div[element-crypto="efectivo"] div[data-baseweb="input"] { background-color: rgba(33, 150, 243, 0.08) !important; border: 1px solid rgba(33, 150, 243, 0.3) !important; }
        div[element-crypto="debito"] div[data-baseweb="input"] { background-color: rgba(255, 235, 59, 0.12) !important; border: 1px solid rgba(255, 235, 59, 0.4) !important; }
        div[element-crypto="transferencia"] div[data-baseweb="input"] { background-color: rgba(255, 152, 0, 0.08) !important; border: 1px solid rgba(255, 152, 0, 0.3) !important; }
        </style>
    """, unsafe_allow_html=True)

def renderizar_sidebar_completa(balances, totales_dia, hoy):
    st.sidebar.header("🗓️ Panel de Control & Estadísticas")
    
    # Identificar quincena actual
    nombre_q = "1ra Quincena" if hoy.day <= 15 else "2da Quincena"
    
    st.sidebar.markdown(f"### 📊 Acumulados Históricos")
    st.sidebar.info(f"**Total ARBA ({nombre_q}):**\n\n {logica.formato_moneda(balances['quincena_obligaciones'])}")
    st.sidebar.success(f"**Total Aranceles Mes:**\n\n {logica.formato_moneda(balances['aranceles_mes'])}")
    st.sidebar.warning(f"**💵 Efectivo Acumulado Caja:**\n\n {logica.formato_moneda(balances['efectivo_acumulado'])}")

    st.sidebar.write("---")
    st.sidebar.markdown("### 📈 Resumen Neto del Día")
    st.sidebar.caption(f"📚 **Aranceles Hoy:** {logica.formato_moneda(totales_dia['aranceles'])}")
    st.sidebar.caption(f"📜 **Sellados Hoy:** {logica.formato_moneda(totales_dia['sellados'])}")
    st.sidebar.caption(f"🚗 **Patentes Hoy:** {logica.formato_moneda(totales_dia['patentes'])}")
    st.sidebar.caption(f"📁 **Otros Hoy:** {logica.formato_moneda(totales_dia['otros'])}")
    st.sidebar.caption(f"📉 **Gastos Hoy:** {logica.formato_moneda(abs(totales_dia['gastos']))}")
    
    st.sidebar.markdown("**Totales por Medio de Pago:**")
    st.sidebar.caption(f"💳 **Total Débito:** {logica.formato_moneda(totales_dia['debito'])}")
    st.sidebar.caption(f"📲 **Total Transferencias:** {logica.formato_moneda(totales_dia['transferencia'])}")
    st.sidebar.markdown(f"⭐ **NETO TOTAL DEL DÍA:**\n\n **{logica.formato_moneda(totales_dia['total_neto'])}**")

    st.sidebar.write("---")
    if hoy.day == 15 or (hoy + timedelta(days=1)).day == 1:
        st.sidebar.error("🚨 **¡HOY CIERRA LA QUINCENA!** Liquidar Obligaciones.")
    if hoy.weekday() == 1:
        st.sidebar.error("🚨 **¡HOY ES MARTES!** Corresponde pagar 'Otros'.")

def renderizar_formulario_cobros(supabase, fk):
    with st.expander("➕ Cargar Cobro / Gasto Combinado Diario", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### **1. Conceptos del Cobro**")
            t_aranceles = st.text_input("Aranceles ($)", key=f"ar_{fk}")
            t_sellados = st.text_input("Sellados ($)", key=f"se_{fk}")
            t_patentes = st.text_input("Patentes ($)", key=f"pa_{fk}")
            t_otros = st.text_input("Otros ($)", key=f"ot_{fk}")
            t_gastos = st.text_input("Gastos / Egresos de Caja ($)", key=f"ga_{fk}")
            
            c_aranceles = logica.limpiar_monto(t_aranceles)
            c_sellados = logica.limpiar_monto(t_sellados)
            c_patentes = logica.limpiar_monto(t_patentes)
            c_otros = logica.limpiar_monto(t_otros)
            c_gastos = logica.limpiar_monto(t_gastos)
            total_conceptos = c_aranceles + c_sellados + c_patentes + c_otros - c_gastos
        
        with col2:
            st.markdown("### **2. Medios de Pago**")
            st.markdown("<b style='color: #1565c0;'>💵 EFECTIVO</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="efectivo">', unsafe_allow_html=True)
            t_efectivo = st.text_input("Efectivo Entregado ($)", key=f"ef_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<b style='color: #fbc02d;'>💳 DÉBITO</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="debito">', unsafe_allow_html=True)
            t_debito = st.text_input("Débito ($)", key=f"de_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<b style='color: #e65100;'>📲 TRANSFERENCIA</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="transferencia">', unsafe_allow_html=True)
            t_transf = st.text_input("Transferencia ($)", key=f"tr_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            efectivo_recibido = logica.limpiar_monto(t_efectivo)
            debito_input = logica.limpiar_monto(t_debito)
            transf_input = logica.limpiar_monto(t_transf)
            
            monto_restante_conceptos = total_conceptos - debito_input - transf_input
            vuelto = max(0.0, efectivo_recibido - monto_restante_conceptos) if efectivo_recibido > 0 or monto_restante_conceptos > 0 else 0.0
            efectivo_neto_caja = monto_restante_conceptos if efectivo_recibido >= monto_restante_conceptos else efectivo_recibido
            total_medios_ingresados = efectivo_recibido + debito_input + transf_input

        with col3:
            st.markdown("### **3. Validación**")
            st.metric(label="Total a Cobrar", value=logica.formato_moneda(total_conceptos))
            if vuelto > 0:
                st.metric(label="💵 VUELTO A ENTREGAR", value=logica.formato_moneda(vuelto), delta="- Dinero a dar", delta_color="inverse")
            else:
                st.metric(label="Total Ingresado", value=logica.formato_moneda(total_medios_ingresados))
                
            observaciones = st.text_input("Observaciones / Nombre del Cliente", key=f"ob_{fk}")
            
            if st.button("💾 Registrar Operación Completa", use_container_width=True):
                if total_conceptos == 0 and total_medios_ingresados == 0:
                    st.error("No podés registrar una operación vacía.")
                elif c_gastos > 0 and (c_aranceles > 0 or c_sellados > 0 or c_patentes > 0 or c_otros > 0):
                    st.error("Por seguridad, cargá los gastos por separado.")
                elif total_medios_ingresados < total_conceptos:
                    st.error(f"❌ ¡ERROR! Dinero insuficiente.")
                else:
                    data_insert = {
                        "detalle": observaciones if observaciones else ("Gasto de Caja" if c_gastos > 0 else "Cobro General"),
                        "aranceles": c_aranceles, 
                        "sellados": c_sellados, 
                        "patentes": c_patentes, 
                        "otros": c_otros,
                        "gastos": -c_gastos if c_gastos > 0 else 0.0,
                        "efectivo": -c_gastos if c_gastos > 0 else efectivo_neto_caja,
                        "debito": debito_input, 
                        "transferencia": transf_input, 
                        "total_neto": total_conceptos
                    }
                    try:
                        supabase.table("movimientos").insert(data_insert).execute()
                        st.session_state["form_key"] = st.session_state.get("form_key", 0) + 1
                        st.toast("Operación guardada en la NUBE")
                        st.switch_page("registro.py")
                    except Exception as err:
                        st.error(f"Error al impactar en Supabase: {err}")
