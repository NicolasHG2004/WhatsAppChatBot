# Citas Médicas
import json
from datetime import date, datetime, timedelta
from dateparser import parse
from config import cliente, twilio_whatsapp, mama_telefono, horario

# Estado de la conversación de la abuela
flujo = {
    "estado": None,          
    "cita_seleccionada": None,
    "campo_a_cambiar": None 
}


def cargar_citas():
    try:
        with open("citas.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def guardar_citas(citas):
    with open("citas.json", "w") as f:
        json.dump(citas, f, ensure_ascii=False, indent=2)

def guardar_cita(Body):
    campos = {}
    for linea in Body.strip().split("\n"):
        if ": " in linea:
            clave, valor = linea.split(": ", 1)
            campos[clave.strip().lower()] = valor.strip()

    fecha_dt = parse(campos.get("fecha", ""), languages=["es"])
    hora_dt  = parse(campos.get("hora",  ""), languages=["es"])

    cita = {
        "nombre": campos.get("cita", ""),
        "para": campos.get("para",""),
        "fecha":  fecha_dt.strftime("%Y-%m-%d") if fecha_dt else "",
        "hora":   hora_dt.strftime("%H:%M")     if hora_dt  else "",
        "lugar":  campos.get("lugar", "")
    }

    citas = cargar_citas()
    citas.append(cita)
    guardar_citas(citas)

def mostrar_citas():
    citas = cargar_citas()
    if not citas:
        cliente.messages.create(
            body="No tiene citas agendadas en este momento.",
            from_=twilio_whatsapp,
            to=mama_telefono
        )
        return
    mensaje = "🗓️ Citas agendadas:\n\n"
    for cita in citas:
        fecha_normal = datetime.strptime(cita['fecha'], "%Y-%m-%d").strftime("%d/%m/%Y")
        hora_normal  = datetime.strptime(cita['hora'],  "%H:%M").strftime("%I:%M %p")
        mensaje += f"• {cita['nombre']} — {fecha_normal} {hora_normal} — {cita['lugar']}\n"
    cliente.messages.create(body=mensaje, from_=twilio_whatsapp, to=mama_telefono)

def mostrar_citas_numeradas():
    citas = cargar_citas()
    if not citas:
        return None
    mensaje = "¿Cuál cita?\n\n"
    for i, cita in enumerate(citas):
        fecha_normal = datetime.strptime(cita['fecha'], "%Y-%m-%d").strftime("%d/%m/%Y")
        hora_normal  = datetime.strptime(cita['hora'],  "%H:%M").strftime("%I:%M %p")
        mensaje += f"{i+1}️⃣ {cita['nombre']} — {fecha_normal} {hora_normal} — {cita['lugar']}\n"
    return mensaje

def mandar_recordatorio_cita(cita, prefijo, persona):
    hora_normal = datetime.strptime(cita['hora'], "%H:%M").strftime("%I:%M %p")
    cliente.messages.create(
        body=(
            f"🗓️ Hola madre, {prefijo}, {persona} tiene una cita de *{cita['nombre']}* "
            f"en {cita['lugar']} a las {hora_normal}"
        ),
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def verificar_citas():
    citas = cargar_citas()
    hoy    = date.today()
    manana = hoy + timedelta(days=1)
    citas_vigentes = []

    for cita in citas:
        if not cita.get("fecha"):
            continue
        fecha = datetime.strptime(cita["fecha"], "%Y-%m-%d").date()
        if fecha < hoy:
            continue 
        citas_vigentes.append(cita)
        if fecha == manana:
            mandar_recordatorio_cita(cita, "mañana", cita["para"])
        elif fecha == hoy:
            hora_cita   = datetime.strptime(f"{hoy} {cita['hora']}", "%Y-%m-%d %H:%M")
            recordar_en = hora_cita - timedelta(hours=1)
            if recordar_en > datetime.now():
                horario.add_job(
                    mandar_recordatorio_cita, 'date',
                    run_date=recordar_en,
                    args=[cita, "en 1 hora", cita["para"]]
                )

    guardar_citas(citas_vigentes)

