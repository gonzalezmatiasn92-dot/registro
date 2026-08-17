import streamlit as st
from conexion import obtener_cliente
from logica import procesar_metricas
from planilladiaria import renderizar_sidebar, renderizar_formulario, renderizar_tabla_movimientos
from cierre import renderizar_cierre_caja
# AGREGADO: Importamos el nuevo centro contable
from informes import renderizar_modulo_exportacion

st.set_page_config(
    page_title="Sistema Integral de Caja",
    layout="wide",
    initial_sidebar_state="expanded"
)

def traer_movimientos_seguros(supabase_client):
    """Descarga los datos exigiendo de forma nativa la columna temporal de Supabase"""
    try:
        respuesta = supabase_client.table("movimientos").select(
            "id, fecha_operacion, detalle, aranceles, sellados, patentes, otros, gastos, efectivo, debito, transferencia, transferencia2, total_neto"
        ).order("id").execute()
        return respuesta.data if respuesta.data else []
    except Exception as e:
        st.error(f"Error crítico en la comunicación con Supabase: {e}")
        return []

def main():
    supabase_client = obtener_cliente()
    todos_los_movimientos = traer_movimientos_seguros(supabase_client)
    
    arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy = procesar_metricas(todos_los_movimientos)
    
    renderizar_sidebar(arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy)
    
    # CORREGIDO: Agregamos la tercera pestaña de Exportación / Auditoría
    pestana_planilla, pestana_cierre, pestana_informes = st.tabs([
        "📝 Planilla Diaria", 
        "🔒 Cierre de Caja / Arqueo",
        "📥 Exportar Informes"
    ])
    
    with pestana_planilla:
        renderizar_formulario(supabase_client)
        renderizar_tabla_movimientos(supabase_client, movimientos_hoy)
        
    with pestana_cierre:
        renderizar_cierre_caja(supabase_client, efectivo_caja, movimientos_hoy)
        
    with pestana_informes:
        # CORREGIDO: Enlazamos el set completo de datos históricos al módulo de descarga
        renderizar_modulo_exportacion(todos_los_movimientos)

if __name__ == "__main__":
    main()
