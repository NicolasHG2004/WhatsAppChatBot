# Recordatorio Medicamentos Papá

import json
from datetime import date
from config import cliente, twilio_whatsapp, mama_telefono

flujo_papa = {
    "pasta_pendiente": None
}

def cargar_estado():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_estado(pasta):
    estado = cargar_estado()
    hoy = date.today().isoformat()
    if hoy not in estado:
        estado[hoy] = {"manana":False, "noche":False}
    estado[hoy][pasta] = True
    with open("data.json", "w") as f:
        json.dump(estado, f)

def recordar_pasta(pasta):
    flujo_papa["pasta_pendiente"] = pasta
    cliente.messages.create(
        body=f"💊 Hola, madre, ¿ya le dio la pasta de la *{pasta}* a mi papá?\n\n1️⃣ Sí, ya se la di\n2️⃣ No todavía",
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def verificar_pasta(pasta):
    estado = cargar_estado()
    if estado.get(date.today().isoformat(), {}).get(pasta):
        return
    flujo_papa["pasta_pendiente"] = pasta 
    cliente.messages.create(
        body=f"⚠️ Madre, aún no hemos registrado que mi papá se tomó la pasta de la *{pasta}* hoy. ¿Ya la tomó?\n\n1️⃣ Sí, ya se la tomó\n2️⃣ No todavía",
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def resumen_semanal():
    estado = cargar_estado()
    mensaje = "📊 Resumen semanal:\n"
    for fecha, pastas in estado.items():
        for horario, tomada in pastas.items():   
            mensaje += f"✅ {fecha} {horario}\n" if tomada else f"❌ {fecha} {horario}\n"
    cliente.messages.create(body=mensaje, from_=twilio_whatsapp, to=mama_telefono)