import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from supabase import create_client, Client

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Control de Caja Profesional", page_icon="💰", layout="wide")

# 🛠️ PEGÁ ACÁ TUS CLAVES REALES DE SUPABASE:
SUPABASE_URL = "https://cbxbzvlxcbflgydzahbx.supabase.co"
SUPABASE_KEY = "sb_publishable_kmJj93r3hj3LyOtVRcqVFw_lqkCMhqO"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as err:
    st.error(f"Error de red: {err}")

# FUNCIÓN PARA DAR FORMATO DE DINERO LOCAL ($ 1.250.000,00)
def formato_moneda(valor):
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# PROCESADOR DE FÓRMULAS AVANZADO CON SOPORTE PARA EL "=" E INGRESO NEGATIVO/POSITIVO
def limpiar_monto(texto):
    if not texto:
        return 0.0
    texto_str = str(texto).strip()
    es_negativo = False
    
    if texto_str.startswith("-"):
        es_negativo = True
        texto_str = texto_str[1:]
    elif texto_str.startswith("=-"):
        es_negativo = True
        texto_str = "=" + texto_str[2:]
        
    if texto_str.startswith("="):
        try:
            formula = texto_str[1:].replace(".", "").replace(",", ".")
            formula_segura = re.sub(r'[^0-9+\-*/().]', '', formula)
            res = float(eval(formula_segura))
            return -res if es_negativo else res
        except:
            return 0.0
    try:
        res = float(texto_str.replace(".", "").replace(",", "."))
        return -res if es_negativo else res
    except:
        return 0.0

# VARIABLES DE CONTROL SÍNCRONAS
if "caja_cerrada" not in st.session_state:
    st.session_state.caja_cerrada = False
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ESTILOS VISUALES: Fondos transparentados muy suaves
st.markdown("""
    <style>
    div[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    div[element-crypto="efectivo"] div[data-baseweb="input"] { background-color: rgba(33, 150, 243, 0.08) !important; border: 1px solid rgba(33, 150, 243, 0.3) !important; }
    div[element-crypto="debito"] div[data-baseweb="input"] { background-color: rgba(255, 235, 59, 0.12) !important; border: 1px solid rgba(255, 235, 59, 0.4) !important; }
    div[element-crypto="transferencia"] div[data-baseweb="input"] { background-color: rgba(255, 152, 0, 0.08) !important; border: 1px solid rgba(255, 152, 0, 0.3) !important; }
    </style>
""", unsafe_allow_html=True)

st.title("💰 Sistema Inteligente de Control de Caja (MODO RED)")
fecha_actual = datetime.now().strftime("%d/%m/%Y")
st.subheader(f"Planilla Diaria - Fecha: {fecha_actual}")

if st.session_state.caja_cerrada:
    st.success("🔒 La caja de hoy ya se encuentra CERRADA. Los datos están congelados.")

# --- TRAER TODO EL HISTORIAL DE LA NUBE EN TIEMPO REAL ---
try:
    response = supabase.table("movimientos").select("*").order("id", desc=False).execute()
    movimientos_nube = response.data
except Exception as e:
    movimientos_nube = []

# --- LÓGICA DE TIEMPOS DINÁMICOS ACUMULATIVOS DE INTERFAZ ---
hoy = datetime.now()
dia_hoy = hoy.day
mes_hoy = hoy.month
anio_hoy = hoy.year

if dia_hoy <= 15:
    inicio_q = datetime(anio_hoy, mes_hoy, 1)
    fin_q = datetime(anio_hoy, mes_hoy, 15)
    nombre_quincena = "1ra Quincena"
else:
    inicio_q = datetime(anio_hoy, mes_hoy, 16)
    siguiente_mes = mes_hoy % 12 + 1
    siguiente_mes_anio = anio_hoy if siguiente_mes > 1 else anio_hoy + 1
    fin_q = datetime(siguiente_mes_anio, siguiente_mes, 1) - timedelta(days=1)
    nombre_quincena = "2da Quincena"

inicio_mes = datetime(anio_hoy, mes_hoy, 1)

# --- MOTORES DE CÁLCULO HISTÓRICO INFINITO ---
tot_efectivo_acumulado = 0.0
saldo_acara = 0.0
saldo_carcos = 0.0
saldo_gastos_generales = 0.0

acumulado_quincena_obligaciones = 0.0
acumulado_aranceles_mes = 0.0

for m in movimientos_nube:
    det = str(m.get("detalle", ""))
    efec = float(m.get("efectivo", 0.0))
    
    tot_efectivo_acumulado += efec
    
    if "Fondo ACARA" in det:
        saldo_acara += efec
    elif "Fondo Carcos" in det:
        saldo_carcos += efec
    elif "Gastos Generales" in det:
        saldo_gastos_generales += efec

    try:
        mov_fecha = datetime.strptime(fecha_actual, "%d/%m/%Y")
        if inicio_q <= mov_fecha <= fin_q:
            acumulado_quincena_obligaciones += float(m.get("sellados", 0.0)) + float(m.get("patentes", 0.0))
        if inicio_mes <= mov_fecha:
            acumulado_aranceles_mes += float(m.get("aranceles", 0.0))
    except:
        pass

# --- BARRA LATERAL: ALERTAS Y CRONOGRAMA ---
st.sidebar.header("🗓️ Alertas de Cronograma")
st.sidebar.markdown(f"### 📊 Acumulado {nombre_quincena}")
st.sidebar.info(f"**Sellados + Patentes:**\n\n {formato_moneda(acumulado_quincena_obligaciones)}")
st.sidebar.markdown(f"### 📈 Acumulado Mensual")
st.sidebar.success(f"**Total Aranceles Mes:**\n\n {formato_moneda(acumulado_aranceles_mes)}")

if dia_hoy == 15 or hoy.day == fin_q.day:
    st.sidebar.error("🚨 **¡HOY CIERRA LA QUINCENA!** Liquidar Sellados y Patentes.")
if hoy.weekday() == 1:
    st.sidebar.error("🚨 **¡HOY ES MARTES!** Corresponde pagar el concepto 'Otros'.")

st.sidebar.write("---")
# --- FORMULARIO DE INGRESO PRINCIPAL (LIMPIO Y OPERATIVO) ---
if not st.session_state.caja_cerrada:
    with st.expander("➕ Cargar Cobro / Gasto Combinado Diario", expanded=True):
        col1, col2, col3 = st.columns(3)
        fk = st.session_state.form_key
        
        with col1:
            st.markdown("### **1. Conceptos del Cobro**")
            t_aranceles = st.text_input("Aranceles ($)", key=f"ar_{fk}")
            t_sellados = st.text_input("Sellados ($)", key=f"se_{fk}")
            t_patentes = st.text_input("Patentes ($)", key=f"pa_{fk}")
            t_otros = st.text_input("Otros ($)", key=f"ot_{fk}")
            t_gastos = st.text_input("Gastos / Egresos de Caja ($)", key=f"ga_{fk}")
            
            c_aranceles = limpiar_monto(t_aranceles)
            c_sellados = limpiar_monto(t_sellados)
            c_patentes = limpiar_monto(t_patentes)
            c_otros = limpiar_monto(t_otros)
            c_gastos = limpiar_monto(t_gastos)
            total_conceptos = c_aranceles + c_sellados + c_patentes + c_otros - c_gastos
        
        with col2:
            st.markdown("### **2. Medios de Pago**")
            st.markdown("<b style='color: #1565c0;'>💵 EFECTIVO</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="efectivo">', unsafe_allow_html=True)
            t_efectivo = st.text_input("Efectivo Entregado ($)", key=f"ef_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<b style='color: #fbc02d;'>💳 DÉBITO</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="debito">', unsafe_allow_html=True)
            t_debito = st.text_input("Débito ($)", key=f"de_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<b style='color: #e65100;'>📲 TRANSFERENCIA</b>", unsafe_allow_html=True)
            st.markdown('<div element-crypto="transferencia">', unsafe_allow_html=True)
            t_transf = st.text_input("Transferencia ($)", key=f"tr_{fk}", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            efectivo_recibido = limpiar_monto(t_efectivo)
            debito_input = limpiar_monto(t_debito)
            transf_input = limpiar_monto(t_transf)
            
            monto_restante_conceptos = total_conceptos - debito_input - transf_input
            vuelto = max(0.0, efectivo_recibido - monto_restante_conceptos) if efectivo_recibido > 0 or monto_restante_conceptos > 0 else 0.0
            efectivo_neto_caja = monto_restante_conceptos if efectivo_recibido >= monto_restante_conceptos else efectivo_recibido
            total_medios_ingresados = efectivo_recibido + debito_input + transf_input

        with col3:
            st.markdown("### **3. Validación**")
            st.metric(label="Total a Cobrar", value=formato_moneda(total_conceptos))
            if vuelto > 0:
                st.metric(label="💵 VUELTO A ENTREGAR", value=formato_moneda(vuelto), delta="- Dinero a dar", delta_color="inverse")
            else:
                st.metric(label="Total Ingresado", value=formato_moneda(total_medios_ingresados))
                
            observaciones = st.text_input("Observaciones / Nombre del Cliente", key=f"ob_{fk}")
            
            if st.button("💾 Registrar Operación Completa", use_container_width=True):
                if total_conceptos == 0 and total_medios_ingresados == 0:
                    st.error("No podés registrar una operación vacía.")
                elif c_gastos > 0 and (c_aranceles > 0 or c_sellados > 0 or c_patentes > 0 or c_otros > 0):
                    st.error("Por seguridad, cargá los gastos por separado.")
                elif total_medios_ingresados < total_conceptos:
                    st.error(f"❌ ¡ERROR! Dinero insuficiente.")
                else:
                    data_insert = {
                        "detalle": observaciones if observaciones else ("Gasto de Caja" if c_gastos > 0 else "Cobro General"),
                        "aranceles": c_aranceles, "sellados": c_sellados, "patentes": c_patentes, "otros": c_otros,
                        "gastos": -c_gastos if c_gastos > 0 else 0.0,
                        "efectivo": -c_gastos if c_gastos > 0 else efectivo_neto_caja,
                        "debito": debito_input, "transferencia": transf_input, "total_neto": total_conceptos
                    }
                    try:
                        supabase.table("movimientos").insert(data_insert).execute()
                        st.session_state.form_key += 1
                        st.toast("Operación guardada en la NUBE")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al impactar en Supabase: {err}")
# --- SECCIÓN 2: PLANILLA DIARIA VISIBLE ---
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
        df_visual_formato[col] = df_visual_formato[col].apply(formato_moneda)
        
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

# --- SECCIÓN 3: TOTALES DIARIOS Y COLECTIVOS ---
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
c1.metric("📚 Aranceles (Hoy)", formato_moneda(tot_aranceles))
c2.metric("📜 Sellados (Hoy)", formato_moneda(tot_sellados))
c3.metric("🚗 Patentes (Hoy)", formato_moneda(tot_patentes))
c4.metric("📁 Otros (Hoy)", formato_moneda(tot_otros))
c5.metric("📉 Gastos (Hoy)", formato_moneda(abs(tot_gastos)))

st.write("### Totales por Medio de Pago Colectivo")
m1, m2, m3, m4 = st.columns(4)
m1.metric("💵 EFECTIVO TOTAL ACUMULADO (En Caja)", formato_moneda(tot_efectivo_acumulado))
m2.metric("💳 Total Débito", formato_moneda(tot_debito))
m3.metric("📲 Total Transferencias", formato_moneda(tot_transf))
m4.metric("⭐ NETO TOTAL DEL DÍA", formato_moneda(tot_general))
# --- SECCIÓN 4: ARQUEO, RETIROS Y FONDOS AL FINAL DEL DIA ---
st.write("---")
st.subheader("🧮 Panel de Cierre de Caja y Arqueo General (Fin del Día)")

col_auditoria, col_billetes, col_validacion = st.columns(3)

with col_auditoria:
    st.markdown("🔒 **1. Validar Totales Diarios de Conceptos:**")
    val_aranceles = st.text_input("Total Aranceles según planilla manual:", key="v_ar")
    val_sellados = st.text_input("Total Sellados según planilla manual:", key="v_se")
    val_patentes = st.text_input("Total Patentes según planilla manual:", key="v_pa")
    
    n_val_aranceles = limpiar_monto(val_aranceles)
    n_val_sellados = limpiar_monto(val_sellados)
    n_val_patentes = limpiar_monto(val_patentes)
    
    st.write("---")
    st.markdown("🏛️ **🏦 Depositar en Banco (Retiro de Efectivo):**")
    t_deposito_banco = st.text_input("Monto exacto a enviar al banco:", key="dep_banco")
    monto_a_dep = limpiar_monto(t_deposito_banco)
    
    if monto_a_dep > 0 and not st.session_state.caja_cerrada:
        if monto_a_dep > tot_efectivo_acumulado:
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
            st.warning(f"✔ Retiro {i+1}: {formato_moneda(abs(d))} asentado en planilla.")

with col_billetes:
    st.markdown("💵 **2. Arqueo de Billetes Físico en Mano:**")
    t_b20000 = st.text_input("Billetes de $20.000:", key="tb20k")
    t_b10000 = st.text_input("Billetes de $10.000:", key="tb10k")
    t_b2000 = st.text_input("Billetes de $2.000:", key="tb2k")
    t_b1000 = st.text_input("Billetes de $1.000:", key="tb1k")
    t_b500 = st.text_input("Billetes de $500:", key="tb500")
    t_b200 = st.text_input("Billetes de $200:", key="tb200")
    t_b100 = st.text_input("Billetes de $100:", key="tb100")

    efectivo_fisico_real = (limpiar_monto(t_b20000)*20000) + (limpiar_monto(t_b10000)*10000) + (limpiar_monto(t_b2000)*2000) + (limpiar_monto(t_b1000)*1000) + (limpiar_monto(t_b500)*500) + (limpiar_monto(t_b200)*200) + (limpiar_monto(t_b100)*100)

    st.write("---")
    st.markdown("💼 **3. Gestión de Fondos Especiales (Suma/Resta):**")
    tipo_fondo = st.selectbox("Seleccione el Fondo:", ["ACARA", "Carcos", "Gastos Generales"])
    t_monto_fondo = st.text_input("Monto (Positivo suma / Negativo resta):", placeholder="Ej: -15000 o 50000", key="f_monto_input")
    monto_fondo_num = limpiar_monto(t_monto_fondo)
    
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
        st.error(f"❌ Error en Aranceles: Sistema dice {formato_moneda(tot_aranceles)} y cargaste {formato_moneda(n_val_aranceles)}")
        error_conceptos = True
    if val_sellados and n_val_sellados != tot_sellados:
        st.error(f"❌ Error en Sellados: Sistema dice {formato_moneda(tot_sellados)} y cargaste {formato_moneda(n_val_sellados)}")
        error_conceptos = True
    if val_patentes and n_val_patentes != tot_patentes:
        st.error(f"❌ Error en Patentes: Sistema dice {formato_moneda(tot_patentes)} y cargaste {formato_moneda(n_val_patentes)}")
        error_conceptos = True
        
    if not error_conceptos and val_aranceles and val_sellados and val_patentes:
        st.success("✅ ¡Conceptos Diarios cruzados con éxito!")
        
    st.write("---")
    st.metric("Efectivo esperado acumulado:", formato_moneda(tot_efectivo_acumulado))
    st.metric("Efectivo real contado:", formato_moneda(efectivo_fisico_real))
    diferencia = efectivo_fisico_real - tot_efectivo_acumulado
    
    if diferencia == 0 and not error_conceptos and val_aranceles and val_sellados and val_patentes:
        st.success("🏆 ¡CAJA TOTALMENTE PERFECTA Y AUDITADA!")
        if not st.session_state.caja_cerrada:
            st.warning("⚠️ **ADVERTENCIA:** Bloqueará la edición en todas las terminales.")
            confirmar_check = st.checkbox("Confirmar cierre general de operaciones")
            if st.button("🔒 Cerrar Caja Definitivamente", disabled=not confirmar_check, type="primary", use_container_width=True):
                st.session_state.caja_cerrada = True
                st.rerun()
    elif diferencia < 0:
        st.error(f"❌ FALTANTE DE EFECTIVO: {formato_moneda(abs(diferencia))}")
    elif diferencia > 0:
        st.warning(f"⚠️ SOBRANTE DE EFECTIVO: {formato_moneda(diferencia)}")
    else:
        st.info("Complete las planillas manuales de conceptos y arqueo para cerrar la caja.")
        
    st.write("---")
    st.markdown("**Saldos de Fondos Permanentes (Acumulados):**")
    st.info(f"💼 **Fondo ACARA:** {formato_moneda(saldo_acara)}\n\n🏢 **Fondo Carcos:** {formato_moneda(saldo_carcos)}\n\n📉 **Gastos Generales:** {formato_moneda(saldo_gastos_generales)}")

# INYECCIÓN DE SCRIPT JAVASCRIPT GLOBAL
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
