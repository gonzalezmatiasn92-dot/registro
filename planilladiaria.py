import streamlit as st
import pandas as pd
import re
from logica import (
    calcular_totales, 
    calcular_medios_pago, 
    guardar_movimiento, 
    eliminar_movimiento, 
    obtener_fecha_argentina,
    parsear_fecha_supabase
)
from colores import aplicar_colores_pasteles

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

def inyectar_estilos_bordes_inputs():
    """Inyecta estilos CSS para colorear los bordes de los inputs según la paleta pastel"""
    st.html("""
        <style>
        /* Conceptos del Cobro */
        div[data-testid="stTextInput"]:has(input[aria-label="Aranceles ($)"]) input { border: 2px solid rgba(180, 180, 180, 0.9) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="Sellados ($)"]) input { border: 2px solid rgba(10, 40, 90, 0.8) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="Patentes ($)"]) input { border: 2px solid rgba(25, 75, 140, 0.7) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="Otros ($)"]) input { border: 2px solid rgba(0, 191, 255, 0.8) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="Gastos / Egresos de Caja ($)"]) input { border: 2px solid rgba(255, 100, 100, 0.8) !important; }
        
        /* Medios de Pago */
        div[data-testid="stTextInput"]:has(input[aria-label="💵 EFECTIVO"]) input { border: 2px solid rgba(100, 220, 100, 0.9) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="💳 DÉBITO"]) input { border: 2px solid rgba(255, 230, 100, 1) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="📲 TRANSFERENCIA 1"]) input { border: 2px solid rgba(255, 140, 0, 0.8) !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="📲 TRANSFERENCIA 2"]) input { border: 2px solid rgba(255, 140, 0, 0.8) !important; }
        </style>
    """)

def renderizar_sidebar(arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy):
    """Sidebar lateral de estadísticas y acumulados"""
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
    """Formulario interactivo de carga diaria con llaves dinámicas basadas en versión"""
    fecha_hoy = obtener_fecha_argentina().strftime("%d/%m/%Y")
    st.subheader(f"Planilla Diaria - Fecha: {fecha_hoy}")
    
    # Inyectamos los marcos de color en la cabecera de forma nativa
    inyectar_estilos_bordes_inputs()
    
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    v = st.session_state.form_version

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 1. Conceptos del Cobro")
        t_aranceles = st.text_input("Aranceles ($)", key=f"f_aran_{v}")
        t_sellados = st.text_input("Sellados ($)", key=f"f_sell_{v}")
        t_patentes = st.text_input("Patentes ($)", key=f"f_pat_{v}")
        t_otros = st.text_input("Otros ($)", key=f"f_otr_{v}")
        t_gastos = st.text_input("Gastos / Egresos de Caja ($)", key=f"f_gast_{v}")
        
        aranceles = evaluar_celda_excel(t_aranceles)
        sellados = evaluar_celda_excel(t_sellados)
        patentes = evaluar_celda_excel(t_patentes)
        otros = evaluar_celda_excel(t_otros)
        gastos = evaluar_celda_excel(t_gastos)
        
    with col2:
        st.markdown("#### 2. Medios de Pago")
        t_efectivo = st.text_input("💵 EFECTIVO", key=f"p_efe_{v}")
        t_debito = st.text_input("💳 DÉBITO", key=f"p_deb_{v}")
        t_transf1 = st.text_input("📲 TRANSFERENCIA 1", key=f"p_tr1_{v}")
        t_transf2 = st.text_input("📲 TRANSFERENCIA 2", key=f"p_tr2_{v}")
        
        efectivo = evaluar_celda_excel(t_efectivo)
        debito = evaluar_celda_excel(t_debito)
        transf1 = evaluar_celda_excel(t_transf1)
        transf2 = evaluar_celda_excel(t_transf2)
        
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
            
        detalle = st.text_input("Observaciones / Nombre del Cliente (Opcional)", key=f"f_det_{v}")
        boton_guardar = st.button("💾 Registrar Operación Completa", use_container_width=True)
        
        if boton_guardar:
            # CORREGIDO: Se incluyó 'operador' en el diccionario de datos enviado a Supabase
            datos = {
                "detalle": detalle.strip() if detalle else "",
                "aranceles": aranceles, "sellados": sellados, "patentes": patentes, "otros": otros, "gastos": gastos,
                "efectivo": efectivo, "debito": debito, "transferencia": transf1, "transferencia2": transf2,
                "total_neto": total_cobrar,
                "operador": st.session_state.get("usuario_activo", "Sistema")
            }
            exito, msj = guardar_movimiento(supabase_client, datos)
            if exito:
                st.session_state.form_version += 1
                st.success(msj)
                st.rerun()
            else:
                st.error(msj)

def renderizar_tabla_movimientos(supabase_client, movimientos_hoy):
    """Muestra transacciones en tiempo real incluyendo la columna de operador activo"""
    st.markdown("---")
    st.subheader("🖥️ Movimientos Sincronizados Hoy (Todas las computadoras)")
    if movimientos_hoy:
        df = pd.DataFrame(movimientos_hoy)
        
        if "fecha_operacion" in df.columns:
            df["fecha_operacion_legible"] = df["fecha_operacion"].apply(
                lambda x: parsear_fecha_supabase(x).strftime("%d/%m/%Y %H:%M") if parsear_fecha_supabase(x) else ""
            )
        else:
            df["fecha_operacion_legible"] = ""

        # CORREGIDO: Añadimos 'operador' a la estructura ordenada de la grilla diaria
        columnas_ordenadas = [
            "id", "fecha_operacion_legible", "operador", "detalle", "aranceles", "sellados", "patentes", 
            "otros", "gastos", "efectivo", "debito", "transferencia", "transferencia2", "total_neto"
        ]
        for col in columnas_ordenadas:
            if col not in df.columns:
                df[col] = 0.0
                
        df = df[columnas_ordenadas]
        
        df_limpio = df.fillna(0.0)
        for col in ["id", "fecha_operacion_legible", "operador", "detalle"]:
            df_limpio[col] = df[col].fillna("").astype(str).replace("None", "")

        df_estilizado = df_limpio.style.apply(aplicar_colores_pasteles, axis=1)
        
        df_estilizado = df_estilizado.format({
            "aranceles": "${:,.2f}", "sellados": "${:,.2f}", "patentes": "${:,.2f}",
            "otros": "${:,.2f}", "gastos": "${:,.2f}", "efectivo": "${:,.2f}",
            "debito": "${:,.2f}", "transferencia": "${:,.2f}", "transferencia2": "${:,.2f}",
            "total_neto": "${:,.2f}"
        })

        st.dataframe(df_estilizado, use_container_width=True, hide_index=True)
        
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
        st.info("No hay movimientos cargados en el día de la fecha.")
