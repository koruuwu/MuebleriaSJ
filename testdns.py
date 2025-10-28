import sys

# 1️⃣ Verificar que psycopg2 esté instalado
try:
    import psycopg2
    print("✅ psycopg2 está instalado")
except ImportError:
    print("❌ psycopg2 NO está instalado")
    sys.exit(1)

# 2️⃣ Leer variables de entorno desde .env
try:
    from decouple import config
    DB_NAME = config("DB_NAME")
    DB_USER = config("DB_USER")
    DB_PASSWORD = config("DB_PASSWORD")
    DB_HOST = config("DB_HOST")
    DB_PORT = config("DB_PORT")
    print("✅ Variables de entorno leídas correctamente")
except Exception as e:
    print("❌ Error leyendo .env:", e)
    sys.exit(1)

import socket
try:
    ip = socket.gethostbyname(DB_HOST)
    print(f"✅ Host resuelto: {DB_HOST} -> {ip}")
except Exception as e:
    print(f"❌ No se pudo resolver el host {DB_HOST}:", e)
    sys.exit(1)

# 4️⃣ Intentar conexión a PostgreSQL
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.close()
    print("✅ Conexión a la base de datos exitosa")
except Exception as e:
    print("❌ No se pudo conectar a la base de datos:", e)
    sys.exit(1)

