from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from Notificaciones.models import Notificacione

def crear_notificacion(tipo, mensaje, objeto=None):
    ct = None
    oid = None

    if objeto:
        ct = ContentType.objects.get_for_model(objeto)
        oid = objeto.pk

    Notificacione.objects.create(
        tipo=tipo,
        mensaje=mensaje,
        creado=timezone.now(),
        leida=False,
        content_type=ct,
        object_id=oid,
    )
