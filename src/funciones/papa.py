# Recordatorio Medicamentos Papá
from datetime import date
from config import cliente, twilio_whatsapp, mama_telefono
from db import get_conn

flujo_papa = {
    "pasta_pendiente": None
}

def cargar_estado():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT fecha, manana, noche FROM pastillas")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row[0]: {"manana": row[1], "noche": row[2]} for row in rows}

def guardar_estado(pasta):
    hoy = date.today().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pastillas (fecha, manana, noche)
        VALUES (%s, FALSE, FALSE)
        ON CONFLICT (fecha) DO NOTHING
    """, (hoy,))
    if pasta == "manana":
        cur.execute("UPDATE pastillas SET manana = TRUE WHERE fecha = %s", (hoy,))
    else:
        cur.execute("UPDATE pastillas SET noche = TRUE WHERE fecha = %s", (hoy,))
    conn.commit()
    cur.close()
    conn.close()

def recordar_pasta(pasta):
    flujo_papa["pasta_pendiente"] = pasta
    cliente.messages.create(
        body=f"💊 Hola, madre, ¿ya le dio la pasta de la *{pasta}* a mi papá?\n\n1️⃣ Sí, ya se la di\n2️⃣ No todavía",
        from_=twilio_whatsapp,
        to=mama_telefono
    )

def verificar_pasta(pasta):
    hoy = date.today().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT manana, noche FROM pastillas WHERE fecha = %s", (hoy,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        tomada = row[0] if pasta == "manana" else row[1]
        if tomada:
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
        for turno, tomada in pastas.items():
            mensaje += f"✅ {fecha} {turno}\n" if tomada else f"❌ {fecha} {turno}\n"
    cliente.messages.create(body=mensaje, from_=twilio_whatsapp, to=mama_telefono)