import streamlit as st
import pandas as pd

def verificar_credenciales(supabase_client, usuario, clave):
    """Verifica si el usuario existe, la clave coincide y está aprobado"""
    try:
        respuesta = supabase_client.table("usuarios").select("*").eq("usuario", usuario.strip()).execute()
        if respuesta.data:
            datos_user = respuesta.data[0]
            if datos_user.get("clave") == clave.strip():
                if datos_user.get("estado") == "Aprobado":
                    return True, "OK", datos_user
                elif datos_user.get("estado") == "Pendiente":
                    return False, "⏳ Tu cuenta está pendiente de aprobación por el Administrador o Encargado.", None
                else:
                    return False, "🔒 Tu cuenta ha sido bloqueada. Contacta al Administrador.", None
            else:
                return False, "❌ Contraseña incorrecta.", None
        return False, "❌ El usuario ingresado no existe.", None
    except Exception as e:
        return False, f"Error de red: {e}", None

def registrar_solicitud_usuario(supabase_client, usuario, clave):
    """Inserta un nuevo empleado en estado Pendiente"""
    try:
        chequeo = supabase_client.table("usuarios").select("id").eq("usuario", usuario.strip()).execute()
        if chequeo.data:
            return False, "❌ Ese nombre de usuario ya está en uso. Elige otro."
        
        datos = {
            "usuario": usuario.strip(),
            "clave": clave.strip(),
            "rol": "Empleado",
            "estado": "Pendiente"
        }
        supabase_client.table("usuarios").insert(datos).execute()
        return True, "✅ Solicitud enviada con éxito. Avisale al Administrador o Encargado para que apruebe tu ingreso."
    except Exception as e:
        return False, f"Error al registrar: {e}"

def actualizar_estado_usuario(supabase_client, user_id, nuevo_estado):
    try:
        supabase_client.table("usuarios").update({"estado": nuevo_estado}).eq("id", user_id).execute()
        return True
    except Exception:
        return False

def actualizar_rol_usuario(supabase_client, user_id, nuevo_rol):
    try:
        supabase_client.table("usuarios").update({"rol": nuevo_rol}).eq("id", user_id).execute()
        return True
    except Exception:
        return False

def renderizar_login_screen(supabase_client):
    """Muestra la interfaz centralizada de Login / Registro"""
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema de Caja</h1>", unsafe_allow_html=True)
    st.write("")
    
    col_izq, col_cen, col_der = st.columns([1, 2, 1])
    with col_cen:
        modo = st.radio("Seleccione una opción:", ["Iniciar Sesión", "Solicitar Cuenta Nueva"], horizontal=True)
        st.markdown("---")
        
        if modo == "Iniciar Sesión":
            u_login = st.text_input("Nombre de Usuario:", key="u_log")
            c_login = st.text_input("Contraseña:", type="password", key="c_log")
            if st.button("🔑 Entrar al Sistema", use_container_width=True, type="primary"):
                if not u_login or not c_login:
                    st.warning("Por favor complete todos los campos.")
                else:
                    exito, msj, datos = verificar_credenciales(supabase_client, u_login, c_login)
                    if exito:
                        st.session_state.autenticado = True
                        st.session_state.usuario_activo = datos["usuario"]
                        st.session_state.rol_activo = datos["rol"]
                        st.success(f"¡Bienvenido {datos['usuario']}!")
                        st.rerun()
                    else:
                        st.error(msj)
                        
        else:
            u_reg = st.text_input("Elija su Nombre de Usuario (Ej: carlos_caja):", key="u_reg")
            c_reg = st.text_input("Elija su Contraseña:", type="password", key="c_reg")
            if st.button("📝 Enviar Solicitud de Alta", use_container_width=True):
                if not u_reg or not c_reg:
                    st.warning("Por favor complete todos los campos.")
                else:
                    exito, msj = registrar_solicitud_usuario(supabase_client, u_reg, c_reg)
                    if exito:
                        st.success(msj)
                    else:
                        st.error(msj)

def renderizar_panel_gestion_personal(supabase_client):
    """Pestaña exclusiva para Administradores y Encargados"""
    st.header("👥 Gestión de Personal y Aprobación de Cuentas")
    st.markdown("---")
    
    try:
        lista_usuarios = supabase_client.table("usuarios").select("*").order("id").execute().data or []
    except Exception as e:
        st.error(f"Error al conectar con la tabla de usuarios: {e}")
        return

    if not lista_usuarios:
        st.info("No hay usuarios registrados en el sistema.")
        return

    pendientes = [u for u in lista_usuarios if u["estado"] == "Pendiente"]
    activos = [u for u in lista_usuarios if u["estado"] in ["Aprobado", "Bloqueado"]]

    st.markdown("### ⏳ 1. Solicitudes de Alta Pendientes")
    if pendientes:
        for p in pendientes:
            col_u, col_r, col_b1, col_b2 = st.columns([2, 1, 1, 1])
            col_u.write(f"**Usuario:** `{p['usuario']}`")
            col_r.write(f"Rol sugerido: {p['rol']}")
            if col_b1.button("✅ Aprobar Acceso", key=f"ap_{p['id']}", use_container_width=True):
                if actualizar_estado_usuario(supabase_client, p['id'], "Aprobado"):
                    st.success(f"Usuario {p['usuario']} aprobado de forma definitiva.")
                    st.rerun()
            if col_b2.button("❌ Rechazar", key=f"rh_{p['id']}", use_container_width=True):
                if actualizar_estado_usuario(supabase_client, p['id'], "Rechazado"):
                    st.rerun()
    else:
        st.info("No hay solicitudes de empleados nuevos esperando aprobación.")

    st.markdown("---")
    st.markdown("### 📋 2. Control de Personal Activo / Bloqueo")
    
    if activos:
        df_activos = pd.DataFrame(activos)
        df_vista = df_activos[["id", "usuario", "rol", "estado"]].rename(columns={
            "id": "ID", "usuario": "Operador", "rol": "Rol Actual", "estado": "Estado de Acceso"
        })
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
        
        st.markdown("##### Modificar Personal por ID")
        c_id, c_rol, c_est = st.columns(3)
        id_mod = c_id.number_input("ID del personal:", min_value=1, step=1, value=None, key="id_mod_user")
        
        if id_mod:
            user_sel = next((u for u in activos if u["id"] == id_mod), None)
            if user_sel:
                st.write(f"Modificando a: **{user_sel['usuario']}** (Estado actual: {user_sel['estado']} | Rol: {user_sel['rol']})")
                
                with c_rol:
                    nuevo_rol = st.selectbox("Cambiar Rol:", ["Empleado", "Encargado", "Administrador"], index=["Empleado", "Encargado", "Administrador"].index(user_sel["rol"]))
                    if st.button("Guardar Nuevo Rol", key="btn_rol_u"):
                        actualizar_rol_usuario(supabase_client, user_sel["id"], nuevo_rol)
                        st.rerun()
                with c_est:
                    nuevo_est = st.selectbox("Cambiar Acceso:", ["Aprobado", "Bloqueado"], index=["Aprobado", "Bloqueado"].index(user_sel["estado"]))
                    if st.button("Aplicar Estado de Acceso", key="btn_est_u"):
                        actualizar_estado_usuario(supabase_client, user_sel["id"], nuevo_est)
                        st.rerun()
            else:
                st.warning("El ID ingresado no corresponde a ningún usuario activo.")
    else:
        st.info("No hay personal activo cargado en el sistema.")
