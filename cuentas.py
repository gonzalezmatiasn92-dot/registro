import streamlit as st
import pandas as pd
from logica import obtener_fecha_argentina

def verificar_credenciales(supabase_client, usuario, clave):
    try:
        respuesta = supabase_client.table("usuarios").select("*").eq("usuario", usuario.strip()).execute()
        if respuesta.data and len(respuesta.data) > 0:
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
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema de Caja</h1>", unsafe_allow_html=True)
    st.write("")
    
    col_izq, col_cen, col_der = st.columns(3)
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
    st.header("👥 Panel de Gestión de Personal y Reaperturas")
    st.markdown("---")
    
    # 🔓 SECCIÓN CORREGIDA: Muestra las solicitudes de todos los usuarios (incluido Mati / Administrador)
    st.markdown("### 🔓 1. Solicitudes de Reapertura de Caja (Hoy)")
    fecha_hoy_str = obtener_fecha_argentina().strftime("%Y-%m-%d")
    
    try:
        movs_hoy = supabase_client.table("movimientos").select("*").like("fecha_operacion", f"{fecha_hoy_str}%").execute().data or []
        solicitudes = [m for m in movs_hoy if str(m.get("detalle", "")).startswith("SOLICITUD_REAPERTURA:")]
        reaperturas_ya_aprobadas = [m.get("operador") for m in movs_hoy if str(m.get("detalle", "")).startswith("REAPERTURA_APROBADA_")]
    except Exception as e:
        solicitudes = []
        reaperturas_ya_aprobadas = []

    if solicitudes:
        # Contador para filtrar visualmente pedidos activos
        pedidos_visibles = 0
        for sol in solicitudes:
            if sol["operador"] not in reaperturas_ya_aprobadas:
                pedidos_visibles += 1
                c_user, c_mot, c_btn = st.columns(3)
                c_user.write(f"👤 **Usuario:** `{sol['operador']}`")
                motivo_limpio = sol["detalle"].replace("SOLICITUD_REAPERTURA:", "")
                c_mot.write(f"💬 **Motivo:** {motivo_limpio}")
                
                if c_btn.button("🔓 Aprobar Reapertura", key=f"ap_re_{sol['id']}", use_container_width=True):
                    datos_aprobacion = {
                        "detalle": f"REAPERTURA_APROBADA_{fecha_hoy_str}",
                        "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0, "gastos": 0.0,
                        "efectivo": 0.0, "debito": 0.0, "transferencia": 0.0, "transferencia2": 0.0,
                        "total_neto": 0.0,
                        "operador": sol["operador"]
                    }
                    supabase_client.table("movimientos").insert(datos_aprobacion).execute()
                    st.success(f"🔓 Caja desbloqueada para `{sol['operador']}` de forma definitiva.")
                    st.rerun()
        
        if pedidos_visibles == 0:
            st.info("Todas las solicitudes de reapertura de hoy ya fueron autorizadas.")
    else:
        st.info("No hay solicitudes esperando autorización para reabrir planillas hoy.")

    st.markdown("---")
    try:
        lista_usuarios = supabase_client.table("usuarios").select("*").order("id").execute().data or []
    except Exception as e:
        st.error(f"Error al conectar con la tabla de usuarios: {e}")
        return

    pendientes = [u for u in lista_usuarios if u["estado"] == "Pendiente"]
    activos = [u for u in lista_usuarios if u["estado"] in ["Aprobado", "Bloqueado"]]

    st.markdown("### ⏳ 2. Solicitudes de Alta de Empleados")
    if pendientes:
        for p in pendientes:
            col_u, col_r, col_b1, col_b2 = st.columns(4)
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
    st.markdown("### 📋 3. Control de Personal Activo / Bloqueo")
    
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
                st.write(f"Modificando a: **{user_sel['usuario']}**")
                
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
