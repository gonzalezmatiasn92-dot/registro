import streamlit as st
import pandas as pd
from logica import (
    calcular_totales, 
    calcular_medios_pago, 
    guardar_movimiento, 
    eliminar_movimiento, 
    obtener_fecha_argentina
)

def renderizar_sidebar(arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy):
    """Dibuja la barra lateral con nombres visuales y sumas diarias"""
    with st.sidebar:
        st.header("📊 Panel de Control")
        st.markdown("---")
        
        st.markdown("### 📈 Acumulados")
        st.metric(label="ARBA quincena", value=f"${arba_quincena:,.2f}")
        st.metric(label="Aranceles mensual", value=f"${aranceles_mensual:,.2f}")
        st.metric(label="💵 Efectivo Acumulado Caja", value=f"${efectivo_caja:,.2f}")
        
        st.markdown("---")
        
        st.markdown("### 📋 Resumen del Día")
        tot_aran = sum(float(m.get("aranceles") or 0) for m in movimientos_hoy)
        tot_sell = sum(float(m.get("sellados") or 0) for m in movimientos_hoy)
        tot_pate = sum(float(m.get("patentes") or 0) for m in movimientos_hoy)
        tot_gasto = sum(float(m.get("gastos") or 0) for m in movimientos_hoy)
        tot_neto = sum(float(m.get("total_neto") or 0) for m in movimientos_hoy)
        
        st.write(f"• Aranceles: ${tot_aran:,.2f}")
        st.write(f"• Sellados: ${tot_sell:,.2f}")
        st.write(f"• Patentes: ${tot_pate:,.2f}")
        st.write(f"• Gastos: ${tot_gasto:,.2f}")
        st.markdown("**Neto Diario Total:**")
        st.subheader(f"${tot_neto:,.2f}")

def renderizar_formulario(supabase_client):
    """Formulario interactivo de carga limpia sin ceros por defecto"""
    fecha_hoy = obtener_fecha_argentina().strftime("%d/%m/%Y")
    st.subheader(f"Planilla Diaria - Fecha: {fecha_hoy}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 1. Conceptos del Cobro")
        aranceles = st.number_input("Aranceles ($)", min_value=0.0, step=100.0, value=None, key="f_aran")
        sellados = st.number_input("Sellados ($)", min_value=0.0, step=100.0, value=None, key="f_sell")
        patentes = st.number_input("Patentes ($)", min_value=0.0, step=100.0, value=None, key="f_pat")
        otros = st.number_input("Otros ($)", min_value=0.0, step=100.0, value=None, key="f_otr")
        gastos = st.number_input("Gastos / Egresos de Caja ($)", min_value=0.0, step=100.0, value=None, key="f_gast")
        
    with col2:
        st.markdown("#### 2. Medios de Pago")
        efectivo = st.number_input("💵 EFECTIVO", min_value=0.0, step=100.0, value=None, key="p_efe")
        debito = st.number_input("💳 DÉBITO", min_value=0.0, step=100.0, value=None, key="p_deb")
        transf1 = st.number_input("📲 TRANSFERENCIA 1", min_value=0.0, step=100.0, value=None, key="p_tr1")
        transf2 = st.number_input("📲 TRANSFERENCIA 2", min_value=0.0, step=100.0, value=None, key="p_tr2")
        
    total_cobrar = calcular_totales(aranceles, sellados, patentes, otros, gastos)
    total_ingresado = calcular_medios_pago(efectivo, debito, transf1, transf2)
    diferencia = round(total_cobrar - total_ingresado, 2)
    
    with col3:
        st.markdown("#### 3. Validación")
        st.metric(label="Total a Cobrar", value=f"${total_cobrar:,.2f}")
        st.metric(label="Total Ingresado", value=f"${total_ingresado:,.2f}")
        
        if diferencia == 0:
            st.success("✅ Caja Balanceada")
        elif diferencia > 0:
            st.warning(f"⚠️ Falta ingresar: ${diferencia:,.2f}")
        else:
            st.info(f"💡 Vuelto / Excedente: ${abs(diferencia):,.2f}")
            
        detalle = st.text_input("Observaciones / Nombre del Cliente (Opcional)", key="f_det")
        boton_guardar = st.button("💾 Registrar Operación Completa", use_container_width=True)
        
        if boton_guardar:
            if diferencia != 0:
                st.error("Los conceptos y los medios de pago deben coincidir perfectamente para poder guardar.")
            else:
                detalle_final = detalle.strip() if detalle else ""
                datos = {
                    "detalle": detalle_final,
                    "aranceles": aranceles or 0.0,
                    "sellados": sellados or 0.0,
                    "patentes": patentes or 0.0,
                    "otros": otros or 0.0,
                    "gastos": gastos or 0.0,
                    "efectivo": efectivo or 0.0,
                    "debito": debito or 0.0,
                    "transferencia": transf1 or 0.0,
                    "transferencia2": transf2 or 0.0,
                    "total_neto": total_cobrar
                }
                exito, msj = guardar_movimiento(supabase_client, datos)
                if exito:
                    st.success(msj)
                    st.rerun()
                else:
                    st.error(msj)

def renderizar_tabla_movimientos(supabase_client, movimientos_hoy):
    """Muestra exclusivamente las transacciones sincronizadas pertenecientes al día actual"""
    st.markdown("---")
    st.subheader("🖥️ Movimientos Sincronizados Hoy (Todas las computadoras)")
    
    if movimientos_hoy:
        df = pd.DataFrame(movimientos_hoy)
        columnas_ordenadas = [
            "id", "detalle", "aranceles", "sellados", "patentes", 
            "otros", "gastos", "efectivo", "debito", 
            "transferencia", "transferencia2", "total_neto"
        ]
        for col in columnas_ordenadas:
            if col not in df.columns:
                df[col] = 0.0
                
        df = df[columnas_ordenadas]
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("##### 🗑️ Corrección de Registros")
        col_id, col_btn = st.columns(2)
        with col_id:
            id_eliminar = st.number_input("ID del movimiento", min_value=1, step=1, value=None, key="id_del")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Eliminar Registro Erróneo", type="secondary"):
                if id_eliminar:
                    exito, msj = eliminar_movimiento(supabase_client, id_eliminar)
                    if exito:
                        st.success(msj)
                        st.rerun()
                    else:
                        st.error(msj)
                else:
                    st.warning("Seleccione un ID válido.")
    else:
        st.info("No hay movimientos cargados en el día de la fecha.")
