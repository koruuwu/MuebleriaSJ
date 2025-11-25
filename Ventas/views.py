from django.shortcuts import render
from Muebles.models import Mueble
from django.http import JsonResponse
# Create your views here.
def obtener_precio_mueble(request, pk):
    try:
        mueble = Mueble.objects.get(pk=pk)
        return JsonResponse({"precio": mueble.precio_base})
    except Mueble.DoesNotExist:
        return JsonResponse({"precio": 0})