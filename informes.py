import streamlit as st
import pandas as pd
from io import BytesIO
from logica import parsear_fecha_supabase, obtener_fecha_argentina

def generar_excel_contable(df_filtrado):
    """
    Genera un archivo binario de Excel (.xlsx) formateado de manera profesional
    utilizando un buffer de memoria BytesIO.
    """
    output = BytesIO()
    
    # Columnas ordenadas y limpias para el contador
    columnas_reporte = [
        "id", "fecha_operacion_legible", "detalle", "aranceles", "sellados", "patentes", 
        "otros", "gastos", "efectivo", "debito", "transferencia", "transferencia2", "total_neto"
    ]
    
    # Filtrarnos y ordenamos el DataFrame con los nombres finales
    df_excel = df_filtrado[columnas_reporte].copy()
    df_excel = df_excel.rename(columns={
        "id": "ID",
        "fecha_operacion_legible": "Fecha / Hora",
        "detalle": "Detalle / Cliente",
        "aranceles": "Aranceles ($)",
        "sellados": "Sellados ($)",
        "patentes": "Patentes ($)",
        "otros": "Otros ($)",
        "gastos": "Gastos ($)",
        "efectivo": "Efectivo ($)",
        "debito": "Débito ($)",
        "transferencia": "Transferencia 1 ($)",
        "transferencia2": "Transferencia 2 ($)",
        "total_neto": "Total Neto ($)"
    })

    # Escritura del archivo mediante pandas y openpyxl en segundo plano
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_excel.to_excel(writer, index=False, sheet_name="Auditoria de Caja")
        
        # Accedemos a la hoja para autoajustar los anchos de columna de forma prolija
        workbook = writer.book
        worksheet = writer.sheets["Auditoria de Caja"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for col_cell in col for cell in [col_cell])
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    return output.getvalue()

def renderizar_modulo_exportacion(todos_los_movimientos):
    """Interfaz gráfica de auditoría contable con filtros cruzados"""
    st.header("📥 Centro de Exportación de Informes y Auditoría")
    st.markdown("---")
    
    if not todos_los_movimientos:
        st.info("No hay datos históricos registrados en el sistema para auditar.")
        return

    # 1. Preparación del DataFrame base con fechas legibles de control
    df_base = pd.DataFrame(todos_los_movimientos)
    
    def extraer_componentes_fecha(x):
        dt = parsear_fecha_supabase(x)
        if dt:
            return dt.strftime("%d/%m/%Y %H:%M"), dt.strftime("%Y-%m-%d"), str(dt.month), str(dt.year)
        return "", "", "", ""

    # Mapeamos las columnas temporales para los selectores de Streamlit
    fechas_info = df_base["fecha_operacion"].apply(extraer_componentes_fecha)
    df_base["fecha_operacion_legible"] = [f[0] for f in fechas_info]
    df_base["filtro_dia"] = [f[1] for f in fechas_info]
    df_base["filtro_mes"] = [f[2] for f in fechas_info]
    df_base["filtro_anio"] = [f[3] for f in fechas_info]

    # Rellenamos nulos numéricos obligatorios
    columnas_num = ["aranceles", "sellados", "patentes", "otros", "gastos", "efectivo", "debito", "transferencia", "transferencia2", "total_neto"]
    for col in columnas_num:
        df_base[col] = pd.to_numeric(df_base[col]).fillna(0.0)
    df_base["detalle"] = df_base["detalle"].fillna("").astype(str).replace("None", "")

    # 2. Barra de Filtros en 3 Columnas independientes
    st.markdown("#### 🔍 1. Seleccione el rango contable a exportar")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filtro = st.selectbox(
            "Tipo de búsqueda:",
            ["Por Día Exacto", "Por Mes Completo", "Por Año Completo", "Exportar Todo el Historial"]
        )

    df_filtrado = df_base.copy()
    ahora_arg = obtener_fecha_argentina()

    with col2:
        if tipo_filtro == "Por Día Exacto":
            dia_sel = st.date_input("Seleccione el día:", value=ahora_arg.date())
            df_filtrado = df_filtrado[df_filtrado["filtro_dia"] == dia_sel.strftime("%Y-%m-%d")]
            
        elif tipo_filtro == "Por Mes Completo":
            meses_dict = {
                "1": "Enero", "2": "Febrero", "3": "Marzo", "4": "Abril", "5": "Mayo", "6": "Junio",
                "7": "Julio", "8": "Agosto", "9": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
            }
            mes_sel_cod = st.selectbox(
                "Seleccione el mes:",
                options=list(meses_dict.keys()),
                format_func=lambda x: meses_dict[x],
                index=int(ahora_arg.month) - 1
            )
            df_filtrado = df_filtrado[df_filtrado["filtro_mes"] == mes_sel_cod]

    with col3:
        if tipo_filtro in ["Por Mes Completo", "Por Año Completo"]:
            anios_disponibles = sorted(list(df_base["filtro_anio"].unique()), reverse=True)
            anio_sel = st.selectbox("Seleccione el año:", options=anios_disponibles, index=0)
            df_filtrado = df_filtrado[df_filtrado["filtro_anio"] == anio_sel]

    # 3. Métricas de Control y Vista Previa
    st.markdown("---")
    st.markdown("#### 📊 2. Resumen del Período Seleccionado")
    
    registros_encontrados = len(df_filtrado)
    st.write(f"Se encontraron **{registros_encontrados}** movimientos en el rango seleccionado.")

    if registros_encontrados > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cobrado Neto", f"${df_filtrado['total_neto'].sum():,.2f}")
        c2.metric("Total ARBA", f"${(df_filtrado['sellados'].sum() + df_filtrado['patentes'].sum()):,.2f}")
        c3.metric("Total Aranceles", f"${df_filtrado['aranceles'].sum():,.2f}")
        c4.metric("Efectivo Ingresado", f"${df_filtrado['efectivo'].sum():,.2f}")

        # Grilla plana de lectura rápida pre-descarga
        columnas_vista = ["id", "fecha_operacion_legible", "detalle", "total_neto", "efectivo", "debito", "transferencia", "transferencia2"]
        df_vista = df_filtrado[columnas_vista].rename(columns={
            "id": "ID", "fecha_operacion_legible": "Fecha / Hora", "detalle": "Detalle", 
            "total_neto": "Total Neto", "efectivo": "Efectivo", "debito": "Débito"
        })
        st.dataframe(df_vista, use_container_width=True, hide_index=True)

        # 4. Generación y Botón de Descarga Nictitante
        st.markdown("#### 💾 3. Emitir Planilla Oficial")
        
        # Ejecutamos el compilador binario del excel
        datos_excel = generar_excel_contable(df_filtrado)
        
        nombre_archivo = f"auditoria_caja_{tipo_filtro.replace(' ', '_').lower()}.xlsx"
        
        st.download_button(
            label="📥 Descargar Planilla de Excel (.xlsx)",
            data=datos_excel,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning("No se registran movimientos grabados en Supabase que coincidan con los filtros seleccionados.")
