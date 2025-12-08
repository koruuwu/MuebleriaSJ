document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const cotizacionId = params.get("cotizacion_id");

    if (!cotizacionId) return;

    fetch(`/admin/Ventas/ordenesventa/detalles-cotizacion/${cotizacionId}/`)
        .then(res => res.json())
        .then(detalles => {
            if (!detalles || detalles.length === 0) return;

            const addBtn = document.querySelector('.add-row a');

            detalles.forEach((d, index) => {
                // Verificar si el inline existe, si no, agregar
                let muebleSelect = document.querySelector(`#id_detallesordene_set-${index}-id_mueble`);
                if (!muebleSelect && addBtn) {
                    addBtn.click();
                    muebleSelect = document.querySelector(`#id_detallesordene_set-${index}-id_mueble`);
                }

                if (!muebleSelect) return; // si sigue sin existir, saltar

                // Setear Select2
                $(muebleSelect).val(d.mueble).trigger('change');

                const precioInput = document.querySelector(`#id_detallesordene_set-${index}-precio_unitario`);
                if (precioInput) precioInput.value = d.precio;

                const cantidadInput = document.querySelector(`#id_detallesordene_set-${index}-cantidad`);
                if (cantidadInput) cantidadInput.value = d.cantidad;

                const subtotalInput = document.querySelector(`#id_detallesordene_set-${index}-subtotal`);
                if (subtotalInput) subtotalInput.value = d.subtotal;
            });
        });
});
