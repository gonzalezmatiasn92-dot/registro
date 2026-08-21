import streamlit as st
import re
import pandas as pd
from logica import obtener_fecha_argentina, parsear_fecha_supabase

def extraer_ingresos_galicia(texto_bruto):
    """Escanea el copiado del Banco Galicia y extrae montos positivos con sus fechas"""
    ingresos_banco = []
    if not texto_bruto:
        return ingresos_banco
        
    lineas = texto_bruto.split('\n')
    for linea in lineas:
        linea_limpia = linea.strip()
        match_fecha = re.match(r"^(\d{2}/\d{2}/\d{4})", linea_limpia)
        if match_fecha:
            fecha_str = match_fecha.group(1)
            
            if "-$" in linea_limpia or "- " in linea_limpia or ("-" in linea_limpia and re.search(r"-\d", linea_limpia)):
                continue
            
            match_monto = re.search(r"\$(\d{1,3}(?:\.\d{3})*,\d{2})", linea_limpia)
            if not match_monto:
                match_monto = re.search(r"\$(\d+,\d{2})", linea_limpia)
                
            if match_monto:
                monto_texto = match_monto.group(1)
                monto_float = float(monto_texto.replace(".", "").replace(",", "."))
                
                if monto_float > 0:
                    ingresos_banco.append({
                        "fecha": fecha_str,
                        "monto": monto_float
                    })
    return ingresos_banco

def renderizar_modulo_transferencias(supabase_client):
    st.header("📲 Monitor y Conciliación Mutua de Transferencias")
    st.markdown("---")

    # 🕹️ MANDOS DE RENDIMIENTO: Controles superiores para agilizar el sistema
    col_cant, col_est = st.columns(2)
    
    with col_cant:
        # CORREGIDO: Se eliminó la coma duplicada de la sintaxis para que envíe el número limpio
        limite_filas = st.selectbox("📥 Cantidad a mostrar:", [10, 25, 50, 100, 150], index=1)
        
    with col_est:
        filtro_estado = st.radio(
            "🔍 Filtrar por estado de auditoría:",
            ["📋 Ver Todas", "🔴 Ver solo Pendientes", "🟩 Ver solo Validadas"],
            horizontal=True
        )
        
    st.markdown("---")

    # 📥 DESCARGA OPTIMIZADA: Pasamos la variable limite_filas directo a Supabase
    movimientos_sistema = []
    try:
        respuesta = supabase_client.table("movimientos").select(
            "id, fecha_operacion, operador, detalle, transferencia, transferencia2"
        ).order("id", desc=True).limit(limite_filas).execute()
        
        if respuesta.data:
            for m in respuesta.data:
                t1 = float(m.get("transferencia") or 0.0)
                t2 = float(m.get("transferencia2") or 0.0)
                if t1 > 0 or t2 > 0:
                    dt_ope = parsear_fecha_supabase(m.get("fecha_operacion"))
                    fecha_legible = dt_ope.strftime("%d/%m/%Y") if dt_ope else ""
                    
                    detalle_original = m.get("detalle", "") or ""
                    ya_conciliado_historico = "[CONCILIADO]" in detalle_original
                    detalle_limpio = detalle_original.replace("[CONCILIADO]", "").strip()
                    
                    movimientos_sistema.append({
                        "id": m.get("id"),
                        "fecha": fecha_legible,
                        "operador": m.get("operador", "Sistema"),
                        "detalle_completo": detalle_original,
                        "detalle": detalle_limpio if detalle_limpio else "Sin observaciones",
                        "monto": t1 + t2,
                        "ya_conciliado_historico": ya_conciliado_historico
                    })
    except Exception as e:
        st.error(f"Error al descargar registros de Supabase: {e}")
        return

    if not movimientos_sistema:
        st.info("No se encontraron registros de transferencias en el mostrador para el rango seleccionado.")
        return

    col_izq, col_der = st.columns([1.5, 2], gap="large")

    with col_izq:
        st.markdown("### 📥 Buzón Banco Galicia")
        st.write("Pegue el historial de movimientos del Homebanking para cruzar en vivo:")
        texto_banco = st.text_area(label="Buzon Galicia", placeholder="Pegue los datos aquí...", height=180, label_visibility="collapsed", key="txt_galicia_cruz")
        
        ejecutar_escaneo = st.button("🔍 Iniciar Sincronización Mutua", type="primary", use_container_width=True)
        
    lista_banco = extraer_ingresos_galicia(texto_banco) if ejecutar_escaneo else []
    depositos_banco_disponibles = list(lista_banco)

    with col_der:
        st.markdown("### 🖥️ Panel de Control de Caja")
        st.write("Modifique los filtros superiores para cambiar los rangos en pantalla:")
        st.write("")

        tarjetas_dibujadas = 0

        for m_sis in movimientos_sistema:
            match_auto = None
            if not m_sis["ya_conciliado_historico"] and depositos_banco_disponibles:
                for dep_bco in depositos_banco_disponibles:
                    if round(m_sis["monto"], 2) == round(dep_bco["monto"], 2) and m_sis["fecha"] == dep_bco["fecha"]:
                        match_auto = dep_bco
                        break
                if match_auto:
                    depositos_banco_disponibles.remove(match_auto)
                    try:
                        nuevo_detalle = f"{m_sis['detalle_completo']} [CONCILIADO]".strip()
                        supabase_client.table("movimientos").update({"detalle": nuevo_detalle}).eq("id", m_sis["id"]).execute()
                        m_sis["ya_conciliado_historico"] = True
                    except Exception:
                        pass

            es_verde = m_sis["ya_conciliado_historico"]
            if filtro_estado == "🔴 Ver solo Pendientes" and es_verde:
                continue
            if filtro_estado == "🟩 Ver solo Validadas" and not es_verde:
                continue

            tarjetas_dibujadas += 1

            if es_verde:
                est_color = "rgba(40, 167, 69, 0.12)"
                est_borde = "1px solid #28a745"
                est_texto = "🟩 CONCILIADO Y ASENTADO EN HISTORIAL"
                accion_modo = "desvalidar"
            else:
                est_color = "rgba(255, 75, 75, 0.08)"
                est_borde = "1px solid #ff4b4b"
                est_texto = "🔴 PENDIENTE EN BANCO"
                accion_modo = "validar"

            c_info, c_acc = st.columns(2)
            
            c_info.markdown(f"""
                <div style="background-color: {est_color}; border: {est_borde}; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
                    <span style="font-size: 15px; font-weight: bold; color: #111111; display: block;">
                        ID: {m_sis['id']} | {m_sis['fecha']} | {m_sis['operador']} | <span style="color: #0056b3;">${m_sis['monto']:,.2f}</span>
                    </span>
                    <small style="color: #444444; font-size: 13px; display: block; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {m_sis['detalle']}
                    </small>
                    <span style="font-size: 11px; font-weight: bold; margin-top: 6px; display: block; color: #333333;">{est_texto}</span>
                </div>
            """, unsafe_allow_html=True)

            c_acc.write("") 
            if list(m_sis.keys()):
                if accion_modo == "validar":
                    if c_acc.button("✔ Validar", key=f"btn_val_{m_sis['id']}", use_container_width=True, type="secondary"):
                        nuevo_detalle = f"{m_sis['detalle_completo']} [CONCILIADO]".strip()
                        supabase_client.table("movimientos").update({"detalle": nuevo_detalle}).eq("id", m_sis["id"]).execute()
                        st.rerun()
                elif accion_modo == "desvalidar":
                    if c_acc.button("✖ Deshacer", key=f"btn_des_{m_sis['id']}", use_container_width=True, type="secondary"):
                        texto_removido = m_sis['detalle_completo'].replace("[CONCILIADO]", "").strip()
                        supabase_client.table("movimientos").update({"detalle": texto_removido}).eq("id", m_sis["id"]).execute()
                        st.rerun()

        if tarjetas_dibujadas == 0:
            st.info("No hay transferencias registradas que cumplan con el criterio del filtro seleccionado.")

        if depositos_banco_disponibles and ejecutar_escaneo:
            st.markdown("---")
            st.markdown(f"#### 🟦 Dinero flotante detectado en Banco sin rendir en Caja ({len(depositos_banco_disponibles)})")
            df_flo = pd.DataFrame(depositos_banco_disponibles).rename(columns={
                "fecha": "Fecha Banco", "monto": "Monto en Cuenta ($)"
            })
            st.dataframe(df_flo, use_container_width=True, hide_index=True)
