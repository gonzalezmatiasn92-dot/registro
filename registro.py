import streamlit as st
import pandas as pd
from datetime import datetime
import conexion
import logica
import componentes

# 1. INICIALIZACIÓN Y PROTOCOLO DE CONEXIÓN REMOTA
supabase = conexion.obtener_cliente()
componentes.inyectar_estilos()

st.title("💰 Sistema Inteligente de Control de Caja (MODO RED)")
fecha_actual = datetime.now().strftime("%d/%m/%Y")
st.subheader(f"Planilla Diaria - Fecha: {fecha_actual}")

if "caja_cerrada" not in st.session_state:
    st.session_state.caja_cerrada = False
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if st.session_state.caja_cerrada:
    st.success("🔒 La caja de hoy ya se encuentra CERRADA. Los datos están congelados.")

# 2. PROCESAMIENTO MATEMÁTICO HISTÓRICO EN RED
movimientos_nube = conexion.traer_movimientos(supabase)
balances = logica.calcular_balances_historicos(movimientos_nube, fecha_actual)

# 3. RENDERIZADO DE LA BARRA LATERAL
componentes.renderizar_sidebar(balances, datetime.now())

# 4. FORMULARIO PRINCIPAL DE COBROS DIARIOS
if not st.session_state.caja_cerrada:
    componentes.renderizar_formulario_cobros(supabase, st.session_state.form_key)

# 5. PLANILLA VISIBLE SINCRONIZADA
st.write("---")
st.subheader("📋 Movimientos Sincronizados Hoy (Todas las computadoras)")
depositos_hoy_lista = []

if len(movimientos_nube) > 0:
    df = pd.DataFrame(movimientos_nube)
    columnas_orden = ["id", "detalle", "aranceles", "sellados", "patentes", "otros", "gastos", "efectivo", "debito", "transferencia", "total_neto"]
    df_visual = df[columnas_orden].copy()
    
    for index, row in df_visual.iterrows():
        det_str = str(row["detalle"])
        if det_str == "Depósito en Banco":
            depositos_hoy_lista.append(float(row["efectivo"]))
            df_visual.at[index, "detalle"] = "🏛️ DEPOSITADO EN BANCO"
        elif "Movimiento Permanente - Fondo" in det_str:
            df_visual.at[index, "detalle"] = det_str.replace("Movimiento Permanente - ", "💼 ")
            
    df_visual_formato = df_visual.copy()
    for col in ["aranceles", "sellados", "patentes", "otros", "gastos", "efectivo", "debito", "transferencia", "total_neto"]:
        df_visual_formato[col] = df_visual_formato[col].apply(logica.formato_moneda)
        
    st.dataframe(df_visual_formato.set_index("id"), use_container_width=True)
    
    if not st.session_state.caja_cerrada:
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            id_eliminar = st.number_input("ID a eliminar por error (Cobro, Gasto, Fondo o Depósito):", min_value=1, step=1, value=None, placeholder="ID")
            if id_eliminar and st.button("❌ Eliminar de la Nube / Deshacer Acción", type="primary", use_container_width=True):
                supabase.table("movimientos").delete().eq("id", id_eliminar).execute()
                st.toast("Registro eliminado con éxito")
                st.rerun()
else:
    st.info("No hay registros guardados en la nube para el día de hoy.")
# 6. MÉTRICAS DIARIAS Y MEDIOS DE PAGO COLECTIVOS
st.write("---")
st.subheader("📊 Totales Generales de la Oficina (Consolidado Histórico)")

tot_aranceles = sum(float(m.get("aranceles", 0.0)) for m in movimientos_nube)
tot_sellados = sum(float(m.get("sellados", 0.0)) for m in movimientos_nube)
tot_patentes = sum(float(m.get("patentes", 0.0)) for m in movimientos_nube)
tot_otros = sum(float(m.get("otros", 0.0)) for m in movimientos_nube)
tot_gastos = sum(float(m.get("gastos", 0.0)) for m in movimientos_nube)
tot_debito = sum(float(m.get("debito", 0.0)) for m in movimientos_nube)
tot_transf = sum(float(m.get("transferencia", 0.0)) for m in movimientos_nube)
tot_general = sum(float(m.get("total_neto", 0.0)) for m in movimientos_nube)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📚 Aranceles (Hoy)", logica.formato_moneda(tot_aranceles))
c2.metric("📜 Sellados (Hoy)", logica.formato_moneda(tot_sellados))
c3.metric("🚗 Patentes (Hoy)", logica.formato_moneda(tot_patentes))
c4.metric("📁 Otros (Hoy)", logica.formato_moneda(tot_otros))
c5.metric("📉 Gastos (Hoy)", logica.formato_moneda(abs(tot_gastos)))

st.write("### Totales por Medio de Pago Colectivo")
m1, m2, m3, m4 = st.columns(4)
m1.metric("💵 EFECTIVO TOTAL ACUMULADO (En Caja)", logica.formato_moneda(balances["efectivo_acumulado"]))
m2.metric("💳 Total Débito", logica.formato_moneda(tot_debito))
m3.metric("📲 Total Transferencias", logica.formato_moneda(tot_transf))
m4.metric("⭐ NETO TOTAL DEL DÍA", logica.formato_moneda(tot_general))

# 7. PANEL DE CIERRE DE CAJA, ARQUEO Y BALANCES PERMANENTES
st.write("---")
st.subheader("🧮 Panel de Cierre de Caja y Arqueo General (Fin del Día)")
col_auditoria, col_billetes, col_validacion = st.columns(3)

with col_auditoria:
    st.markdown("🔒 **1. Validar Totales Diarios de Conceptos:**")
    val_aranceles = st.text_input("Total Aranceles según planilla manual:", key="v_ar")
    val_sellados = st.text_input("Total Sellados según planilla manual:", key="v_se")
    val_patentes = st.text_input("Total Patentes según planilla manual:", key="v_pa")
    n_val_aranceles = logica.limpiar_monto(val_aranceles)
    n_val_sellados = logica.limpiar_monto(val_sellados)
    n_val_patentes = logica.limpiar_monto(val_patentes)
    
    st.write("---")
    st.markdown("🏛️ **🏦 Depositar en Banco (Retiro de Efectivo):**")
    t_deposito_banco = st.text_input("Monto exacto a enviar al banco:", key="dep_banco")
    monto_a_dep = logica.limpiar_monto(t_deposito_banco)
    
    if monto_a_dep > 0 and not st.session_state.caja_cerrada:
        if monto_a_dep > balances["efectivo_acumulado"]:
            st.error("No podés retirar más efectivo del que hay acumulado.")
        else:
            if st.button("🏦 Confirmar y Registrar Depósito Bancario", use_container_width=True):
                dep_insert = {
                    "detalle": "Depósito en Banco", "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0,
                    "gastos": 0.0, "efectivo": -monto_a_dep, "debito": 0.0, "transferencia": 0.0, "total_neto": 0.0
                }
                supabase.table("movimientos").insert(dep_insert).execute()
                st.toast("Depósito registrado con éxito")
                st.rerun()
                
    if len(depositos_hoy_lista) > 0:
        st.write("---")
        st.markdown("📌 **Depósitos Realizados Hoy:**")
        for i, d in enumerate(depositos_hoy_lista):
            st.warning(f"✔ Retiro {i+1}: {logica.formato_moneda(abs(d))} asentado en planilla.")

with col_billetes:
    st.markdown("💵 **2. Arqueo de Billetes Físico en Mano:**")
    t_b20000 = st.text_input("Billetes de $20.000:", key="tb20k")
    t_b10000 = st.text_input("Billetes de $10.000:", key="tb10k")
    t_b2000 = st.text_input("Billetes de $2.000:", key="tb2k")
    t_b1000 = st.text_input("Billetes de $1.000:", key="tb1k")
    t_b500 = st.text_input("Billetes de $500:", key="tb500")
    t_b200 = st.text_input("Billetes de $200:", key="tb200")
    t_b100 = st.text_input("Billetes de $100:", key="tb100")
    
    efectivo_fisico_real = (logica.limpiar_monto(t_b20000)*20000) + (logica.limpiar_monto(t_b10000)*10000) + (logica.limpiar_monto(t_b2000)*2000) + (logica.limpiar_monto(t_b1000)*1000) + (logica.limpiar_monto(t_b500)*500) + (logica.limpiar_monto(t_b200)*200) + (logica.limpiar_monto(t_b100)*100)

    st.write("---")
    st.markdown("💼 **3. Gestión de Fondos Especiales (Suma/Resta):**")
    tipo_fondo = st.selectbox("Seleccione el Fondo:", ["ACARA", "Carcos", "Gastos Generales"])
    t_monto_fondo = st.text_input("Monto (Positivo suma / Negativo resta):", placeholder="Ej: -15000 o 50000", key="f_monto_input")
    monto_fondo_num = logica.limpiar_monto(t_monto_fondo)
    
    if monto_fondo_num != 0 and not st.session_state.caja_cerrada:
        if st.button(f"🚀 Ajustar Cuenta {tipo_fondo}", use_container_width=True):
            fondo_insert = {
                "detalle": f"Movimiento Permanente - Fondo {tipo_fondo}", "aranceles": 0.0, "sellados": 0.0, "patentes": 0.0, "otros": 0.0,
                "gastos": 0.0, "efectivo": monto_fondo_num, "debito": 0.0, "transferencia": 0.0, "total_neto": 0.0
            }
            supabase.table("movimientos").insert(fondo_insert).execute()
            st.toast("Fondo actualizado")
            st.rerun()

with col_validacion:
    st.markdown("### 📊 Resultado de la Auditoría")
    error_conceptos = False
    if val_aranceles and n_val_aranceles != tot_aranceles:
        st.error(f"❌ Error en Aranceles: Sistema dice {logica.formato_moneda(tot_aranceles)} y cargaste {logica.formato_moneda(n_val_aranceles)}")
        error_conceptos = True
    if val_sellados and n_val_sellados != tot_sellados:
        st.error(f"❌ Error en Sellados: Sistema dice {logica.formato_moneda(tot_sellados)} y cargaste {logica.formato_moneda(n_val_sellados)}")
        error_conceptos = True
    if val_patentes and n_val_patentes != tot_patentes:
        st.error(f"❌ Error en Patentes: Sistema dice {logica.formato_moneda(tot_patentes)} y cargaste {logica.formato_moneda(n_val_patentes)}")
        error_conceptos = True
        
    if not error_conceptos and val_aranceles and val_sellados and val_patentes:
        st.success("✅ ¡Conceptos Diarios cruzados con éxito!")
        
    st.write("---")
    st.metric("Efectivo esperado acumulado:", logica.formato_moneda(balances["efectivo_acumulado"]))
    st.metric("Efectivo real contado:", logica.formato_moneda(efectivo_fisico_real))
    diferencia = efectivo_fisico_real - balances["efectivo_acumulado"]
    
    if diferencia == 0 and not error_conceptos and val_aranceles and val_sellados and val_patentes:
        st.success("🏆 ¡CAJA TOTALMENTE PERFECTA Y AUDITADA!")
        if not st.session_state.caja_cerrada:
            st.warning("⚠️ **ADVERTENCIA:** Bloqueará la edición en todas las terminales.")
            confirmar_check = st.checkbox("Confirmar cierre general de operaciones")
            if st.button("🔒 Cerrar Caja Definitivamente", disabled=not confirmar_check, type="primary", use_container_width=True):
                st.session_state.caja_cerrada = True
                st.rerun()
    elif diferencia < 0:
        st.error(f"❌ FALTANTE DE EFECTIVO: {logica.formato_moneda(abs(diferencia))}")
    elif diferencia > 0:
        st.warning(f"⚠️ SOBRANTE DE EFECTIVO: {logica.formato_moneda(diferencia)}")
    else:
        st.info("Complete las planillas manuales de conceptos y arqueo para cerrar la caja.")
        
    st.write("---")
    st.markdown("**Saldos de Fondos Permanentes (Acumulados):**")
    st.info(f"💼 **Fondo ACARA:** {logica.formato_moneda(balances['acara'])}\n\n🏢 **Fondo Carcos:** {logica.formato_moneda(balances['carcos'])}\n\n📉 **Gastos Generales:** {logica.formato_moneda(balances['gastos_generales'])}")

# INYECCIÓN DE SCRIPT JAVASCRIPT GLOBAL MÁSCARA ADAPTATIVA
st.markdown(
    """
    <script>
    function formatearTodoEnVivo() {
        const inputs = window.parent.document.querySelectorAll('input');
        inputs.forEach(input => {
            if (!input.dataset.maskGlobalAttached) {
                input.addEventListener('input', (e) => {
                    let val = e.target.value.trim();
                    if (val.startsWith("=") || val.startsWith("-") || val.startsWith("=-") || input.type === "number") return;
                    let value = val.replace(/\\D/g, "");
                    if (value === "") { e.target.value = ""; return; }
                    e.target.value = parseInt(value, 10).toLocaleString('de-DE');
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
                input.dataset.maskGlobalAttached = true;
            }
        });
    }
    setInterval(formatearTodoEnVivo, 200);
    </script>
    """,
    unsafe_allow_html=True
)

# BOTÓN DE REINICIO DE PLANILLA
if st.sidebar.button("🔄 Reiniciar aplicación (Pruebas)"):
    st.session_state.movimientos = []
    st.session_state.caja_cerrada = False
    st.rerun()
