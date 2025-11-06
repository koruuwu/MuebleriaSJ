from supabase import create_client
from decouple import config

SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_KEY = config("SUPABASE_KEY")

# Crear el cliente
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_archivo(archivo, carpeta):
    nombre_archivo = archivo.name
    contenido = archivo.read()
    ruta = f"{carpeta}/{nombre_archivo}"
    storage = supabase.storage  # No llamas como función
    print("Supabase:", supabase)
    print("Tipo de supabase.storage:", type(storage))
    print("Tipo de storage:", type(storage))
    print("Métodos en storage:", dir(storage))

    # Subir archivo
    storage.from_("Imagenes").upload(ruta, contenido, {"content-type": archivo.content_type})

    # Obtener URL pública
    url = storage.from_("Imagenes").get_public_url(ruta)
    print("URL pública:", url)
    return ruta, url