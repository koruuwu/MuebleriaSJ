document.addEventListener("DOMContentLoaded", function () {

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/");
        const adminIndex = parts.indexOf("admin");
        return parts.slice(0, adminIndex + 3).join("/");
    }
    const adminBase = getAdminBaseUrl();
    console.log("Admin Base:", adminBase);

    function conectarEventosFila(fila) {
        if (!fila) return;

        const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
        const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
        const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
        const subtotalInput = fila.querySelector('input[id$="-subtotal"]');

        if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) {
            // muestra qué falta si algo no coincide
            console.warn("Fila incompleta, faltan campos:", {
                fila,
                muebleSelect: !!muebleSelect,
                precioInput: !!precioInput,
                cantidadInput: !!cantidadInput,
                subtotalInput: !!subtotalInput
            });
            return;
        }

        // handler que hace el fetch y actualiza precio + subtotal
        function handleSelectChange() {
            const muebleId = muebleSelect.value;
            if (!muebleId) return;
            console.log("Seleccionado muebleId:", muebleId);

            fetch(`${adminBase}/obtener_precio_mueble/${muebleId}/`)
                .then(r => {
                    // para debug: si no es json, lo imprimimos
                    const ct = r.headers.get("content-type") || "";
                    if (!ct.includes("application/json")) {
                        return r.text().then(t => { throw new Error("No JSON: " + t); });
                    }
                    return r.json();
                })
                .then(data => {
                    console.log("Respuesta AJAX:", data);
                    if (data.precio !== undefined) {
                        // escribe el valor en el input y fuerza evento input para que se recalcule
                        precioInput.value = data.precio;
                        precioInput.dispatchEvent(new Event('input', { bubbles: true }));
                        // recalcular subtotal inmediatamente
                        const cantidad = parseFloat(cantidadInput.value) || 0;
                        subtotalInput.value = (cantidad * parseFloat(precioInput.value || 0)).toFixed(2);
                    }
                })
                .catch(err => console.error("Error fetch precio:", err));
        }

        // 1) Manejar cambio nativo
        muebleSelect.addEventListener("change", handleSelectChange);

        // 2) Si existe jQuery + select2, también ligamos el evento select2:select
        if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
            try {
                window.jQuery(muebleSelect).on('select2:select select2:close change', function () {
                    // small delay por si Select2 actualiza valor después
                    setTimeout(handleSelectChange, 10);
                });
            } catch (e) {
                console.warn("No se pudo ligar select2 events:", e);
            }
        }

        // recalcular subtotal cuando cambie cantidad o precio manualmente
        function actualizarSubtotal() {
            const cantidad = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;
            subtotalInput.value = (cantidad * precio).toFixed(2);
        }
        cantidadInput.addEventListener("input", actualizarSubtotal);
        precioInput.addEventListener("input", actualizarSubtotal);
    }

    // conectar a filas ya existentes
    document.querySelectorAll('[id^="detallecotizaciones_set-"][id$="-id_mueble"]').forEach(select => {
        const fila = select.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related');
        conectarEventosFila(fila);
    });

    // conectar a filas nuevas creadas dinámicamente por formset
    document.body.addEventListener("formset:added", function (event) {
        conectarEventosFila(event.target);
    });

});
