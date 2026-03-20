import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # Tabla para las pastillas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pastillas (
            fecha TEXT PRIMARY KEY,
            manana BOOLEAN DEFAULT FALSE,
            noche  BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Tabla para las citas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            para   TEXT,
            fecha  TEXT,
            hora   TEXT,
            lugar  TEXT
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

init_db()