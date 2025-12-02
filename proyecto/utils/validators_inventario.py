from django.core.exceptions import ValidationError
from django.utils import timezone
from Compras.models import InventarioMueble
from Ventas.models import DetallesOrdene
from Empleados.models import PerfilUsuario

class ValidacionInventarioMixin:

    def validar_inventario(self, request, orden, formsets):
        """
        Valida inventario antes de guardar la orden.
        Retorna lista de errores. NO guarda inventario aquí.
        """
        errores = []

        # Obtener sucursal desde el perfil del usuario logeado
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        sucursal = getattr(perfil, "sucursal", None)

        if not sucursal:
            errores.append("El usuario logeado no tiene una sucursal asignada.")
            return errores

        # Validación por cada detalle de la orden
        for formset in formsets:
            if formset.model == DetallesOrdene:
                for detalle_form in formset:

                    if not detalle_form.cleaned_data:
                        continue

                    if detalle_form.cleaned_data.get("DELETE", False):
                        continue

                    mueble = detalle_form.cleaned_data.get("id_mueble")
                    cantidad = detalle_form.cleaned_data.get("cantidad")

                    if not mueble or not cantidad:
                        continue

                    inventario = InventarioMueble.objects.filter(
                        id_mueble=mueble,
                        ubicación=sucursal,
                        estado=True
                    ).first()

                    if not inventario:
                        errores.append(
                            f"No hay inventario disponible para {mueble.nombre} "
                            f"en la sucursal {sucursal}"
                        )
                    elif inventario.cantidad_disponible < cantidad:
                        errores.append(
                            f"Stock insuficiente para {mueble.nombre}. "
                            f"Disponible: {inventario.cantidad_disponible}, "
                            f"Solicitado: {cantidad}"
                        )

        return errores

    def actualizar_inventario(self, orden, request):
        """
        Descuenta inventario cuando ya se guardó la orden.
        """
        perfil = PerfilUsuario.objects.filter(user=request.user).first()
        sucursal = getattr(perfil, "sucursal", None)

        if not sucursal:
            return

        detalles = DetallesOrdene.objects.filter(id_orden=orden)

        for d in detalles:
            inventario = InventarioMueble.objects.filter(
                id_mueble=d.id_mueble,
                ubicación=sucursal,
                estado=True
            ).first()

            if inventario and inventario.cantidad_disponible >= d.cantidad:
                inventario.cantidad_disponible -= d.cantidad
                inventario.ultima_salida = timezone.now().date()
                inventario.save()
