import streamlit as st
from datetime import datetime
import pytz
from supabase import Client

def obtener_fecha_argentina():
    """Retorna la fecha y hora actual en la zona horaria de Argentina"""
    tz = pytz.timezone('America/Buenos_Aires')
    return datetime.now(tz)

def parsear_fecha_supabase(fecha_str):
    """Convierte el timestamp nativo de Supabase a la hora real de Argentina"""
    if not fecha_str:
        return None
    try:
        clean_str = fecha_str.replace('Z', '+00:00')
        dt_utc = datetime.fromisoformat(clean_str)
        tz_arg = pytz.timezone('America/Buenos_Aires')
        return dt_utc.astimezone(tz_arg)
    except Exception:
        return None

def calcular_totales(aranceles, sellados, patentes, otros, gastos):
    return float((aranceles or 0) + (sellados or 0) + (patentes or 0) + (otros or 0) - (gastos or 0))

def calcular_medios_pago(efectivo, debito, transf1, transf2):
    return float((efectivo or 0) + (debito or 0) + (transf1 or 0) + (transf2 or 0))

def guardar_movimiento(supabase_client: Client, datos: dict):
    try:
        supabase_client.table("movimientos").insert(datos).execute()
        return True, "Operación asentada exitosamente."
    except Exception as e:
        return False, f"Error al guardar: {e}"

def eliminar_movimiento(supabase_client: Client, id_movimiento: int):
    try:
        supabase_client.table("movimientos").delete().eq("id", id_movimiento).execute()
        return True, f"Registro ID {id_movimiento} eliminado."
    except Exception as e:
        return False, f"Error al eliminar: {e}"

def procesar_metricas(todos_los_movimientos):
    """Procesa quincenas, meses y discrimina de forma estricta el efectivo acumulado total del efectivo de hoy"""
    ahora = obtener_fecha_argentina()
    hoy_str = ahora.strftime("%Y-%m-%d")
    mes_actual = ahora.month
    anio_actual = ahora.year
    dia_actual = ahora.day
    
    es_primera_quincena = dia_actual <= 15

    arba_quincena = 0.0
    aranceles_mensual = 0.0
    efectivo_acumulado_total = 0.0
    efectivo_hoy = 0.0
    movimientos_hoy = []

    for m in todos_los_movimientos:
        dt_mov = parsear_fecha_supabase(m.get("fecha_operacion")) or ahora
        mov_fecha_str = dt_mov.strftime("%Y-%m-%d")
        
        detalle = str(m.get("detalle") or "")
        sellados = float(m.get("sellados") or 0)
        patentes = float(m.get("patentes") or 0)
        aranceles = float(m.get("aranceles") or 0)
        gastos = float(m.get("gastos") or 0)
        efectivo = float(m.get("efectivo") or 0)

        if dt_mov.month == mes_actual and dt_mov.year == anio_actual:
            aranceles_mensual += aranceles

        if dt_mov.month == mes_actual and dt_mov.year == anio_actual:
            if es_primera_quincena and dt_mov.day <= 15:
                arba_quincena += (sellados + patentes)
            elif not es_primera_quincena and dt_mov.day > 15:
                arba_quincena += (sellados + patentes)

        # CÓMPUTO DE CUENTAS ESTANCAS PERPETUAS
        if "Apertura de Caja" not in detalle:
            efectivo_acumulado_total += (efectivo - gastos)

        # CÓMPUTO ESPECÍFICO DEL DÍA EN CURSO (Para conciliar solo lo de hoy)
        if mov_fecha_str == hoy_str:
            movimientos_hoy.append(m)
            if "Apertura de Caja" not in detalle:
                efectivo_hoy += (efectivo - gastos)

    # Inyectamos de forma temporal el efectivo neto de hoy en st.session_state para que lo lea el arqueo
    st.session_state["efectivo_neto_hoy"] = efectivo_hoy

    return arba_quincena, aranceles_mensual, efectivo_acumulado_total, movimientos_hoy

def calcular_arqueo_fisico(b20k, b10k, b2k, b1k, b500, b200, b100):
    return float((b20k or 0)*20000 + (b10k or 0)*10000 + (b2k or 0)*200 + (b1k or 0)*1000 + (b500 or 0)*500 + (b200 or 0)*200 + (b100 or 0)*100)

def calcular_solo_cambio_chico(b2k, b1k, b500, b200, b100):
    return float((b2k or 0)*2000 + (b1k or 0)*1000 + (b500 or 0)*500 + (b200 or 0)*200 + (b100 or 0)*100)
