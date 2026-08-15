import streamlit as st
from supabase import create_client, Client

# CONEXIÓN OFICIAL EN RED DE TU PROYECTO
SUPABASE_URL = "https://cbxbzvlxcbflgydzahbx.supabase.co"
SUPABASE_KEY = "sb_publishable_kmJj93r3hj3LyOtVRcqVFw_lqkCMhqO"

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa la conexión con el servidor remoto de Supabase"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_cliente():
    try:
        return init_supabase()
    except Exception as err:
        st.error(f"Error crítico de red en conexión.py: {err}")
        return None

def traer_movimientos(supabase: Client):
    """Descarga todo el historial contable desde internet"""
    try:
        response = supabase.table("movimientos").select("*").order("id", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        return []
