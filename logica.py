import streamlit as st
from datetime import datetime
import pytz
from supabase import Client

def obtener_fecha_argentina():
    """Retorna la fecha y hora actual en la zona horaria de Argentina"""
    tz = pytz.timezone('America/Buenos_Aires')
    return datetime.now(tz)

def parsear_fecha_supabase(fecha_str):
    """Convierte el timestamp con zona horaria de Supabase al objeto datetime de Argentina"""
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
    """Calcula el total a cobrar neto de la operación"""
    return float((aranceles or 0) + (sellados or 0) + (patentes or 0) + (otros or 0) - (gastos or 0))

def calcular_medios_pago(efectivo, debito, transf1, transf2):
    """Suma los medios de ingreso digital y físico"""
    return float((efectivo or 0) + (debito or 0) + (transf1 or 0) + (transf2 or 0))

def guardar_movimiento(supabase_client: Client, datos: dict):
    """Inserta el registro en la base de datos"""
    try:
        supabase_client.table("movimientos").insert(datos).execute()
        return True, "Operación asentada exitosamente."
    except Exception as e:
        return False, f"Error de red al guardar: {e}"

def eliminar_movimiento(supabase_client: Client, id_movimiento: int):
    """Elimina permanentemente un registro de la base de datos por su ID"""
    try:
        supabase_client.table("movimientos").delete().eq("id", id_movimiento).execute()
        return True, f"Registro ID {id_movimiento} eliminado."
    except Exception as e:
        return False, f"Error al eliminar: {e}"

def procesar_metricas(todos_los_movimientos):
    """Filtra y procesa los acumulados históricos y del día bajo hora argentina"""
    ahora = obtener_fecha_argentina()
    hoy_str = ahora.strftime("%Y-%m-%d")
    mes_actual = ahora.month
    anio_actual = ahora.year
    dia_actual = ahora.day
    
    es_primera_quincena = dia_actual <= 15

    arba_quincena = 0.0
    aranceles_mensual = 0.0
    efectivo_acumulado_caja = 0.0
    movimientos_hoy = []

    for m in todos_los_movimientos:
        dt_mov = parsear_fecha_supabase(m.get("created_at")) or ahora
        mov_fecha_str = dt_mov.strftime("%Y-%m-%d")
        
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

        # Restamos los gastos/retiros del flujo total acumulado de efectivo
        efectivo_acumulado_caja += (efectivo - gastos)

        if mov_fecha_str == hoy_str:
            movimientos_hoy.append(m)

    return arba_quincena, aranceles_mensual, efectivo_acumulado_caja, movimientos_hoy

def calcular_arqueo_fisico(b20k, b10k, b2k, b1k, b500, b200, b100):
    """Multiplica la cantidad de unidades por su denominación monetaria real"""
    total = ((b20k or 0) * 20000 + 
             (b10k or 0) * 10000 + 
             (b2k or 0) * 2000 + 
             (b1k or 0) * 1000 + 
             (b500 or 0) * 500 + 
             (b200 or 0) * 200 + 
             (b100 or 0) * 100)
    return float(total)
