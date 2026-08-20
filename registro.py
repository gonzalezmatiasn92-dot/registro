import streamlit as st
from conexion import obtener_cliente
from logica import procesar_metricas
from planilladiaria import renderizar_sidebar, renderizar_formulario, renderizar_tabla_movimientos
from cierre import renderizar_cierre_caja
from informes import renderizar_modulo_exportacion
from cuentas import renderizar_login_screen, renderizar_panel_gestion_personal
# INCORPORADO: Importamos la nueva función del asistente de mails y liquidación parcial
from utilidades import renderizar_panel_utilidades

st.set_page_config(
    page_title="Sistema Integral de Caja",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialización obligatoria de las variables de control de sesión en memoria
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = ""
if "rol_activo" not in st.session_state:
    st.session_state.rol_activo = ""

def traer_movimientos_seguros(supabase_client):
    """Descarga los datos exigiendo de forma nativa la columna del operador activo"""
    try:
        respuesta = supabase_client.table("movimientos").select(
            "id, fecha_operacion, operador, detalle, aranceles, sellados, patentes, otros, gastos, efectivo, debito, transferencia, transferencia2, total_neto"
        ).order("id").execute()
        return respuesta.data if respuesta.data else []
    except Exception as e:
        st.error(f"Error crítico en la comunicación con Supabase: {e}")
        return []
def main():
    # Inicializar cliente único de Supabase de la planilla
    supabase_client = obtener_cliente()
    
    # FILTRO DE SEGURIDAD INTERNO: Si no inició sesión, bloquea la app y muestra el login
    if not st.session_state.autenticado:
        renderizar_login_screen(supabase_client)
        return

    # Si el usuario pasó exitosamente la pantalla de ingreso, se habilita la app
    todos_los_movimientos = traer_movimientos_seguros(supabase_client)
    arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy = procesar_metricas(todos_los_movimientos)
    
    # Dibujamos las estadísticas fijas en la barra lateral izquierda
    renderizar_sidebar(arba_quincena, aranceles_mensual, efectivo_caja, movimientos_hoy)
    
    # Inyectamos de forma prolija en el sidebar el nombre de usuario activo y un botón para salir
    with st.sidebar:
        st.markdown("---")
        st.write(f"👤 **Usuario:** `{st.session_state.usuario_activo}`")
        st.write(f"⚙️ **Rol:** {st.session_state.rol_activo}")
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.autenticado = False
            st.session_state.usuario_activo = ""
            st.session_state.rol_activo = ""
            st.rerun()

    # INCORPORADO: Añadimos '🧰 Utilidades' en la botonera de navegación de pestañas
    tabs_nombres = ["📝 Planilla Diaria", "🔒 Cierre de Caja / Arqueo", "🧰 Utilidades", "📥 Exportar Informes"]
    
    # Si ingresa el Dueño (Administrador) o el Encargado Titular, se inyecta la solapa administrativa al final
    if st.session_state.rol_activo in ["Administrador", "Encargado"]:
        tabs_nombres.append("👥 Gestión de Personal")
        
    pestanas = st.tabs(tabs_nombres)
    
    with pestanas[0]:
        renderizar_formulario(supabase_client)
        renderizar_tabla_movimientos(supabase_client, movimientos_hoy)
        
    with pestanas[1]:
        renderizar_cierre_caja(supabase_client, efectivo_caja, movimientos_hoy)
        
    with pestanas[2]:
        # INCORPORADO: Renderizado dinámico del panel de e-mails y Excel de patentes
        renderizar_panel_utilidades()
        
    with pestanas[3]:
        renderizar_modulo_exportacion(todos_los_movimientos)
        
    # Condicional de renderizado exclusivo en pantalla para el bloque administrativo (Desplazado al índice 4)
    if st.session_state.rol_activo in ["Administrador", "Encargado"]:
        with pestanas[4]:
            renderizar_panel_gestion_personal(supabase_client)

if __name__ == "__main__":
    main()
