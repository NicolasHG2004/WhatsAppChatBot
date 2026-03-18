import re
from datetime import datetime, timedelta
from dateparser import parse
from fastapi import FastAPI, Form
from config import cliente, twilio_whatsapp, mama_telefono, horario
from src.funciones.citas_medicas import cargar_citas, guardar_cita, guardar_citas, mostrar_citas, mostrar_citas_numeradas, verificar_citas, flujo_citas_medicas  
from src.funciones.papa import guardar_estado, recordar_pasta, resumen_semanal, verificar_pasta, flujo_papa

app = FastAPI()

horario.add_job(recordar_pasta, 'cron', hour=1,  minute=0,  args=["noche"])   # 8pm Colombia
horario.add_job(recordar_pasta, 'cron', hour=11, minute=30, args=["mañana"])  # 6:30am Colombia
horario.add_job(verificar_pasta,'cron', hour=13, minute=0,  args=["mañana"])  # 8am Colombia
horario.add_job(verificar_pasta,'cron', hour=3,  minute=0,  args=["noche"])   # 10pm Colombia
horario.add_job(resumen_semanal,'cron', day_of_week='sun', hour=15, minute=0) # 10am Colombia
horario.add_job(verificar_citas,'cron', hour=11, minute=0) 

MENSAJE_BIENVENIDA = (
    "Hola, madre. Aquí puede gestionar las citas médicas. Puede:\n\n"
    "📋 *Ver citas:* Ver todas las citas agendadas\n"
    "➕ Agendar una cita nueva en este formato:\n\n"
    "*Cita:* Cardiologia\n"
    "*Para:* Mary\n"
    "*Fecha:* 15 de marzo del 2026\n"
    "*Hora:* 2:00 p.m.\n"
    "*Lugar:* Idime Nueva EPS\n\n"
    "✏️ *Cambiar:* Modificar una cita\n"
    "🗑️ *Eliminar:* Eliminar una cita"
)

def enviar(body, to):
    cliente.messages.create(body=body, from_=twilio_whatsapp, to=to)


@app.api_route("/", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

@app.post("/bot")
def bot(From: str = Form(), Body: str = Form()):
    print(f"Mensaje de {From}: {Body}")
    estado = flujo_citas_medicas["estado"]

    if re.search(r"cancelar|salir", Body.lower()):
        flujo_citas_medicas["estado"] = None
        enviar("✅ Operación cancelada.", mama_telefono)
    # Citas Médicas
    elif estado == "mostrar_citas_eliminar":
        citas = cargar_citas()
        if not Body.strip().isdigit():
            enviar("Por favor ingrese un número válido.", mama_telefono)
            enviar(mostrar_citas_numeradas(),mama_telefono)
        else:
            indice = int(Body.strip()) - 1
            if indice < 0 or indice >= len(citas):
                enviar("Ese número no corresponde a ninguna cita.", mama_telefono)
                enviar(mostrar_citas_numeradas(),mama_telefono)
            else:
                cita_eliminada = citas.pop(indice)
                guardar_citas(citas)
                flujo_citas_medicas["estado"] = None
                enviar(f"✅ Cita de *{cita_eliminada['nombre']}* eliminada.", mama_telefono)

    elif estado == "mostrar_citas_cambiar":
        citas = cargar_citas()
        if not Body.strip().isdigit():
            enviar("Por favor ingrese un número válido.", mama_telefono)
            enviar(mostrar_citas_numeradas(),mama_telefono)
        else:
            indice = int(Body.strip()) - 1
            if indice < 0 or indice >= len(citas):
                enviar("Ese número no corresponde a ninguna cita.", mama_telefono)
                enviar(mostrar_citas_numeradas(),mama_telefono)
            else:
                flujo_citas_medicas["cita_seleccionada"] = indice
                flujo_citas_medicas["estado"] = "esperar_campo_cambiar"
                enviar("¿Qué desea cambiar?\n\n1️⃣ Nombre\n2️⃣ Fecha\n3️⃣ Hora\n4️⃣ Lugar", mama_telefono)

    elif estado == "esperar_campo_cambiar":
        campos_map = {1: "nombre", 2: "fecha", 3: "hora", 4: "lugar"}
        if not Body.strip().isdigit() or int(Body.strip()) not in campos_map:
            enviar("Por favor ingrese un número entre 1 y 4.", mama_telefono)
            enviar("¿Qué desea cambiar?\n\n1️⃣ Nombre\n2️⃣ Fecha\n3️⃣ Hora\n4️⃣ Lugar", mama_telefono)
            
        else:
            campo_elegido = campos_map[int(Body.strip())]
            flujo_citas_medicas["campo_a_cambiar"] = campo_elegido
            flujo_citas_medicas["estado"] = "esperar_nuevo_valor"
            enviar(f"¿Cuál es el nuevo valor de {campo_elegido}?", mama_telefono)

    elif estado == "esperar_nuevo_valor":
        citas  = cargar_citas()
        indice = flujo_citas_medicas["cita_seleccionada"]
        campo  = flujo_citas_medicas["campo_a_cambiar"]
        if campo == "fecha":
            valor = parse(Body.strip(), languages=["es"]).strftime("%Y-%m-%d")
        elif campo == "hora":
            valor = parse(Body.strip(), languages=["es"]).strftime("%H:%M")
        else:
            valor = Body.strip()
        citas[indice][campo] = valor
        guardar_citas(citas)
        flujo_citas_medicas["estado"] = "esperar_otro_cambio"
        enviar("✅ Guardado. ¿Desea cambiar otro campo? (si / no)", mama_telefono)

    elif estado == "esperar_otro_cambio":
        if Body.strip().lower() in ["si", "sí"]:
            flujo_citas_medicas["estado"] = "esperar_campo_cambiar"
            enviar("¿Qué desea cambiar?\n\n1️⃣ Nombre\n2️⃣ Fecha\n3️⃣ Hora\n4️⃣ Lugar", mama_telefono)
        else:
            flujo_citas_medicas["estado"] = None
            enviar("✅ Cita actualizada.", mama_telefono)

    
    
    # Citas Médicas Palabras Clave
    elif re.search(r"hola|buenas", Body.lower()):
        enviar(MENSAJE_BIENVENIDA, mama_telefono)

    elif re.search(r"eliminar", Body.lower()):
        mensaje = mostrar_citas_numeradas()
        if not mensaje:
            enviar("No tiene citas agendadas.", mama_telefono)
        else:
            flujo_citas_medicas["estado"] = "mostrar_citas_eliminar"
            enviar(mensaje, mama_telefono)

    elif re.search(r"cambiar|modificar", Body.lower()):
        mensaje = mostrar_citas_numeradas()
        if not mensaje:
            enviar("No tienes citas agendadas.", mama_telefono)
        else:
            flujo_citas_medicas["estado"] = "mostrar_citas_cambiar"
            enviar(mensaje, mama_telefono)

    elif re.search(r"ver citas|mis citas|citas", Body.lower()):
        mostrar_citas()

    elif re.search(r"fecha:", Body.lower()) and re.search(r"hora:", Body.lower()):
        guardar_cita(Body)
        verificar_citas()
        enviar("✅ Cita guardada. Le recordaré el día anterior y 1 hora antes 🗓️", mama_telefono)


    
    
    
    
    # Papá
    elif Body.strip() == "1":
        guardar_estado(flujo_papa["pasta_pendiente"])
        enviar("¡Listo!", From)

    elif Body.strip() == "2":
        enviar("No se le vaya a olvidar darle la pasta más rato", From)
        horario.add_job(verificar_pasta, 'date', run_date=datetime.now() + timedelta(hours=1))
