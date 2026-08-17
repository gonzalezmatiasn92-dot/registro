import streamlit as st
from conexion import obtener_cliente
from logica import procesar_metricas

# Importaciones desde tus nuevos módulos independientes
from planilladiaria import (
    renderizar_sidebar, 
    renderizar_formulario, 
    renderizar_tabla_movimientos
)
from cierre import renderizar_cierre_caja

st.set_page_config(
    page_title="Sistema Integral de Caja",
    layout="wide",
    initial_sidebar_state="expanded"
)

def traer_movimientos_con_fecha(supabase_client):
    """Descarga los registros conteniendo el timestamp de sincronización de Supabase"""
    try:
        respuesta = supabase_client.table("movimientos").select(
            "id, created_at, detalle, aranceles, sellados, patentes, otros, gastos, efectivo, debito, transferencia, transferencia2, total_neto"
        ).order("id").execute()
        return respuesta.data if respuesta.data else []
    except Exception:
        try:
            respuesta = supabase_client.table("movimientos").select(
                "id, detalle, aranceles, sellados, patentes, otros, gastos, efectivo, debito, transferencia, transferencia2, total_neto"
            ).order("id").execute()
            return respuesta.data if respuesta.data else []
        except Exception as e:
            st.error(f"Error crítico en la comunicación con Supabase: {e}")
            return []

def main():
    # Inicializar cliente único de Supabase
    supabase_client = obtener_cliente()
    todos_los_movimientos = traer_movimientos_con_fecha(supabase_client)
    
    # Procesar métricas por zona horaria de Argentina
    arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy = procesar_metricas(todos_los_movimientos)
    
    # Renderizar panel de control lateral fijo (importado de planilladiaria)
    renderizar_sidebar(arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy)
    
    # Crear pestañas principales de la interfaz
    pestana_planilla, pestana_cierre = st.tabs(["📝 Planilla Diaria", "🔒 Cierre de Caja / Arqueo"])
    
    with pestana_planilla:
        renderizar_formulario(supabase_client)
        renderizar_tabla_movimientos(supabase_client, movimientos_hoy)
        
    with pestana_cierre:
        renderizar_cierre_caja(supabase_client, efectivo_caja, movimientos_hoy)

if __name__ == "__main__":
    main()
