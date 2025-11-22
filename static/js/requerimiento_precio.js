document.addEventListener("DOMContentLoaded", function () {
    


    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const adminIndex = parts.indexOf("admin");
        if (adminIndex === -1) return "/admin/";
        // Base: /admin/app/model/
        const baseParts = parts.slice(0, adminIndex + 3);
        return "/" + baseParts.join("/") + "/";
    }

    const adminBase = getAdminBaseUrl();
 

    function conectarFilaRequerimiento(fila) {
        if (!fila) return;

        const materialSelect = fila.querySelector('select[id$="-material"]');
        const proveedorSelect = fila.querySelector('select[id$="-proveedor"]');
        const precioInput = fila.querySelector('input[id$="-precio_actual"]');
        const cantidadInput = fila.querySelector('input[id$="-cantidad_necesaria"]');
        const subtotalInput = fila.querySelector('input[id$="-subtotal"]');
        console.log("DEBUG:", adminBase, materialSelect?.value, proveedorSelect?.value);

        if (!materialSelect || !proveedorSelect || !precioInput || !cantidadInput || !subtotalInput) {
            console.warn("Campos faltantes en fila:", fila);
            return;
        }

        function actualizarPrecio() {
            const materialId = materialSelect.value;
            const proveedorId = proveedorSelect.value;

            if (!materialId || !proveedorId) return;

            fetch(`${adminBase}obtener_precio_material/${materialId}/${proveedorId}/`)
                .then(r => r.json())
                .then(data => {
                    precioInput.value = data.precio || 0;
                    recalcularSubtotal();
                })
                .catch(err => console.error("Error al obtener precio:", err));
        }

        function recalcularSubtotal() {
            const cant = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;
            subtotalInput.value = (cant * precio).toFixed(2);
        }

        // Actualiza precio cuando cambia material o proveedor
        materialSelect.addEventListener("change", actualizarPrecio);
        proveedorSelect.addEventListener("change", actualizarPrecio);

        // Recalcular subtotal al escribir cantidad o precio
        cantidadInput.addEventListener("input", recalcularSubtotal);
        precioInput.addEventListener("input", recalcularSubtotal);

        // Compatibilidad con select2
        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(materialSelect).on("select2:select select2:close change", actualizarPrecio);
            window.jQuery(proveedorSelect).on("select2:select select2:close change", actualizarPrecio);
        }
    }

    // Conectar filas existentes
    document.querySelectorAll('[id^="requerimientomateriale_set-"][id$="-material"]')
        .forEach(select => conectarFilaRequerimiento(select.closest('.inline-related')));

    // Conectar filas nuevas añadidas dinámicamente
    document.body.addEventListener("formset:added", function (event) {
        conectarFilaRequerimiento(event.target);
    });

});
