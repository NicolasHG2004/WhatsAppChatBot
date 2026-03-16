import os
from dotenv import load_dotenv
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
cliente         = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
twilio_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")
mama_telefono   = os.getenv("MAMA_PHONE")
horario         = BackgroundScheduler()
horario.start()