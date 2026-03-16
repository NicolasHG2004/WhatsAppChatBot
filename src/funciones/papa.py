# Recordatorio Medicamentos Papá

import json
from datetime import date
from config import cliente, twilio_whatsapp, mama_telefono

def cargar_estado():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_estado():
    estado = cargar_estado()
    estado[date.today().isoformat()] = True
    with open("data.json", "w") as f:
        json.dump(estado, f)

def recordar_pasta():
    cliente.messages.create(
        body="💊 Hola, madre, ¿ya le dio la  pasta a mi papá?\n\n1️⃣ Sí, ya se la di\n2️⃣ No todavía",
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def verificar_pasta():
    estado = cargar_estado()
    if estado.get(date.today().isoformat()):
        return
    cliente.messages.create(
        body="⚠️ Madre, aún no hemos registrado que mi papá se tomó la pasta hoy. ¿Ya la tomó?\n\n1️⃣ Sí, ya se la tomó\n2️⃣ No todavía",
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def resumen_semanal():
    estado = cargar_estado()
    mensaje = "📊 Resumen semanal:\n"
    for fecha, tomada in estado.items():
        mensaje += f"✅ {fecha}\n" if tomada else f"❌ {fecha}\n"
    cliente.messages.create(body=mensaje, from_=twilio_whatsapp, to=mama_telefono)