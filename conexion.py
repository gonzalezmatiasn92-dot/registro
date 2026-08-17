import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def obtener_cliente() -> Client:
    """Establece la conexión directa forzada con tu base de datos de Supabase"""
    url = "https://cbxbzvlxcbflgydzahbx.supabase.co"
    key = "sb_publishable_kmJj93r3hj3LyOtVRcqVFw_lqkCMhqO"
    return create_client(url, key)

def traer_movimientos(supabase_client: Client):
    """Descarga en tiempo real incluyendo la columna nativa fecha_operacion"""
    try:
        respuesta = supabase_client.table("movimientos").select(
            "id, fecha_operacion, detalle, aranceles, sellados, patentes, otros, gastos, efectivo, debito, transferencia, transferencia2, total_neto"
        ).order("id").execute()
        return respuesta.data if respuesta.data else []
    except Exception as e:
        st.error(f"Error de sincronización en red: {e}")
        return []
