document.addEventListener("DOMContentLoaded", function () {
    const subtotalInput = document.querySelector("#id_subtotal");
    const isvInput = document.querySelector("#id_isv");
    const totalInput = document.querySelector("#id_total");

    if (subtotalInput) subtotalInput.readOnly = true;
    if (isvInput) isvInput.readOnly = true;
    if (totalInput) totalInput.readOnly = true;

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/");
        const adminIndex = parts.indexOf("admin");
        return parts.slice(0, adminIndex + 3).join("/");
    }

    const adminBase = getAdminBaseUrl();
    console.log("Admin Base:", adminBase);

    /* =====================================================
       ============ CÁLCULOS DE LA ORDEN COMPLETA ==========
       ===================================================== */
    function recalcularTotalesOrden() {
        let subtotalGeneral = 0;

        document.querySelectorAll('input[id$="-subtotal"]').forEach(input => {
            subtotalGeneral += parseFloat(input.value) || 0;
        });

        const descuentoInput = document.querySelector("#id_descuento");
        const subtotalInput = document.querySelector("#id_subtotal");
        const isvInput = document.querySelector("#id_isv");
        const totalInput = document.querySelector("#id_total");

        const descuentoPorcentaje = parseFloat(descuentoInput?.value) || 0;
        const descuentoAplicado = subtotalGeneral * (descuentoPorcentaje / 100);
        const isv = subtotalGeneral * 0.15;
        const total = subtotalGeneral + isv - descuentoAplicado;

        if (subtotalInput) subtotalInput.value = subtotalGeneral.toFixed(2);
        if (isvInput) isvInput.value = isv.toFixed(2);
        if (totalInput) totalInput.value = total.toFixed(2);

        if (totalInput) totalInput.dispatchEvent(new Event('totalActualizado'));
    }

    /* =====================================================
       ======= EVENTOS Y CÁLCULO DE CADA FILA DETALLE ======
       ===================================================== */
    function conectarEventosFila(fila) {
        if (!fila) return;

        const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
        const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
        const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
        const subtotalInput = fila.querySelector('input[id$="-subtotal"]');

        if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) return;

        function handleSelectChange() {
            const muebleId = muebleSelect.value;
            if (!muebleId) {
                precioInput.value = "";
                actualizarSubtotalFila();
                return;
            }

            fetch(`${adminBase}/obtener_precio_mueble/${muebleId}/`)
                .then(r => {
                    const ct = r.headers.get("content-type") || "";
                    if (!ct.includes("application/json")) return r.text().then(t => { throw new Error("No JSON: "+t) });
                    return r.json();
                })
                .then(data => {
                    if (data.precio !== undefined) {
                        precioInput.value = data.precio;
                        actualizarSubtotalFila();
                    }
                })
                .catch(err => console.error("Error AJAX precio:", err));
        }

        function actualizarSubtotalFila() {
            const cantidad = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;
            subtotalInput.value = (cantidad * precio).toFixed(2);
            recalcularTotalesOrden();
        }

        muebleSelect.addEventListener("change", handleSelectChange);
        cantidadInput.addEventListener("input", actualizarSubtotalFila);
        precioInput.addEventListener("input", actualizarSubtotalFila);

        // Inicializar subtotal si hay valores
        const cantidadVal = parseFloat(cantidadInput.value) || 0;
        const precioVal = parseFloat(precioInput.value) || 0;
        if (cantidadVal > 0 && precioVal > 0) subtotalInput.value = (cantidadVal * precioVal).toFixed(2);

        // Soporte select2
        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(muebleSelect).on("select2:select select2:close change", function () {
                setTimeout(handleSelectChange, 10);
            });
        }
    }

    // Inicializar cálculos
    function inicializarCalculos() {
        document.querySelectorAll('[id^="detalleCotizaciones_set-"]').forEach(row => {
            const cantidadInput = row.querySelector('input[id$="-cantidad"]');
            const precioInput = row.querySelector('input[id$="-precio_unitario"]');
            const subtotalInput = row.querySelector('input[id$="-subtotal"]');
            if (cantidadInput && precioInput && subtotalInput) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const precio = parseFloat(precioInput.value) || 0;
                subtotalInput.value = (cantidad * precio).toFixed(2);
            }
        });
        recalcularTotalesOrden();
    }

    // Conectar filas existentes
    document.querySelectorAll('[id^="detalleCotizaciones_set-"][id$="-id_mueble"]').forEach(select => {
        const fila = select.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related');
        conectarEventosFila(fila);
    });

    // Conectar filas nuevas
    document.body.addEventListener("formset:added", function (event) {
        setTimeout(() => {
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 50);
    });

    // Recalcular totales cuando cambie descuento
    const descuentoInput = document.querySelector("#id_descuento");
    if (descuentoInput) descuentoInput.addEventListener("input", recalcularTotalesOrden);

    // Inicializar al cargar la página
    setTimeout(() => {
        inicializarCalculos();
        document.querySelectorAll('.form-row, .dynamic-detallecotizaciones_set, .inline-related').forEach(fila => {
            if (fila.querySelector('select[id$="-id_mueble"]') || fila.querySelector('input[id$="-precio_unitario"]')) {
                conectarEventosFila(fila);
            }
        });
    }, 300);

    window.addEventListener('load', function() {
        setTimeout(inicializarCalculos, 200);
    });
});
