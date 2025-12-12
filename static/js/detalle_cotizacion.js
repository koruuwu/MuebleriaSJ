document.addEventListener("DOMContentLoaded", function () {

    /* ============================
       CAMPOS SOLO LECTURA
    ============================ */
    const subtotalInput = document.querySelector("#id_subtotal");
    const isvInput = document.querySelector("#id_isv");
    const totalInput = document.querySelector("#id_total");

    if (subtotalInput) subtotalInput.readOnly = true;
    if (isvInput) isvInput.readOnly = true;
    if (totalInput) totalInput.readOnly = true;

    /* ============================
       BASE URL ADMIN
    ============================ */
    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/");
        const adminIndex = parts.indexOf("admin");
        return parts.slice(0, adminIndex + 3).join("/");
    }

    const adminBase = getAdminBaseUrl();

    /* ============================
       CÁLCULO TOTAL DE ORDEN
    ============================ */
    function recalcularTotalesOrden() {
        let subtotalGeneral = 0;

        document.querySelectorAll('input[id$="-subtotal"]').forEach(input => {
            subtotalGeneral += parseFloat(input.value) || 0;
        });

        const descuentoInput = document.querySelector("#id_descuento");
        const descuentoPorcentaje = parseFloat(descuentoInput?.value) || 0;

        const descuentoAplicado = subtotalGeneral * (descuentoPorcentaje / 100);
        const isv = subtotalGeneral * 0.15;
        const total = subtotalGeneral + isv - descuentoAplicado;

        if (subtotalInput) subtotalInput.value = subtotalGeneral.toFixed(2);
        if (isvInput) isvInput.value = isv.toFixed(2);
        if (totalInput) {
            totalInput.value = total.toFixed(2);
            totalInput.dispatchEvent(new Event('totalActualizado'));
        }
    }

    /* ============================
       CONECTAR EVENTOS EN UNA FILA
    ============================ */
    function conectarEventosFila(fila) {
        if (!fila) return;

        const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
        const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
        const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
        const subtotalInput = fila.querySelector('input[id$="-subtotal"]');
        subtotalInput.readOnly=true;
        precioInput.readOnly=true;

        if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) return;

        subtotalInput.readOnly = true;

        function handleSelectChange() {
            const muebleId = muebleSelect.value;

            if (!muebleId) {
                precioInput.value = "";
                actualizarSubtotalFila();
                return;
            }

            fetch(`${adminBase}/obtener_precio_mueble/${muebleId}/`)
                .then(r => r.json())
                .then(data => {
                    precioInput.value = data.precio;
                    actualizarSubtotalFila();

                    if (window.jQuery && window.jQuery.fn.select2) {
                        window.jQuery(muebleSelect).trigger('change.select2');
                    }
                });
        }

        function actualizarSubtotalFila() {
            const cantidad = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;
            const subtotal = cantidad * precio;

            subtotalInput.value = subtotal.toFixed(2);
            recalcularTotalesOrden();
        }

        muebleSelect.addEventListener("change", handleSelectChange);
        cantidadInput.addEventListener("input", actualizarSubtotalFila);
        precioInput.addEventListener("input", actualizarSubtotalFila);

        const cantidad = parseFloat(cantidadInput.value) || 0;
        const precio = parseFloat(precioInput.value) || 0;

        if (cantidad > 0 && precio > 0) {
            subtotalInput.value = (cantidad * precio).toFixed(2);
            actualizarSubtotalFila();
        }

        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(muebleSelect).off('select2:select'); // limpiar duplicados

            // Evento seguro para carga de precio
            window.jQuery(muebleSelect).on('select2:select', function () {
                handleSelectChange();
            });
        }

    }

    /* ============================
       INICIALIZAR CÁLCULOS
    ============================ */
    function inicializarCalculos() {
        document.querySelectorAll('[id^="detalleCotizaciones_set-"]').forEach(row => {
            const cantidadInput = row.querySelector('input[id$="-cantidad"]');
            const precioInput = row.querySelector('input[id$="-precio_unitario"]');
            const subtotalInput = row.querySelector('input[id$="-subtotal"]');

            if (cantidadInput && precioInput && subtotalInput) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const precio = parseFloat(precioInput.value) || 0;

                if (cantidad > 0 && precio > 0) {
                    subtotalInput.value = (cantidad * precio).toFixed(2);
                }
            }
        });

        recalcularTotalesOrden();
    }

    /* ============================
       CONECTAR TODAS LAS FILAS
    ============================ */
    function conectarTodasLasFilas() {
        document.querySelectorAll('select[id$="-id_mueble"]').forEach(select => {
            const fila = select.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr');
            if (fila) conectarEventosFila(fila);
        });
    }

    /* ============================
       NUEVAS FILAS (formset)
    ============================ */
    document.body.addEventListener("formset:added", function (event) {
        setTimeout(() => {
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 100);
    });

    document.addEventListener("django:formset:added", function(event) {
        setTimeout(() => {
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 100);
    });

    /* ============================
       DESCUENTO
    ============================ */
    const descuentoInput = document.querySelector("#id_descuento");
    if (descuentoInput) {
        descuentoInput.addEventListener("input", recalcularTotalesOrden);
    }

    /* ============================
       INICIALIZACIÓN GLOBAL
    ============================ */
    function inicializarCompleta() {
        conectarTodasLasFilas();
        setTimeout(() => inicializarCalculos(), 200);
        setTimeout(recalcularTotalesOrden, 500);
    }

    setTimeout(inicializarCompleta, 300);

    window.addEventListener('load', () => {
        setTimeout(inicializarCompleta, 200);
    });

    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            setTimeout(inicializarCompleta, 300);
        }
    });

    /* ============================
       BACKUP: LISTENER GLOBAL
    ============================ */
    document.addEventListener('input', function(event) {
        const target = event.target;

        if (target && (target.matches('input[id$="-cantidad"]') ||
                       target.matches('input[id$="-precio_unitario"]'))) {

            const fila = target.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr');
            if (!fila) return;

            const subtotalInput = fila.querySelector('input[id$="-subtotal"]');
            const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
            const precioInput = fila.querySelector('input[id$="-precio_unitario"]');

            if (subtotalInput && cantidadInput && precioInput) {
                subtotalInput.value = ( (parseFloat(cantidadInput.value)||0) *
                                        (parseFloat(precioInput.value)||0) ).toFixed(2);
                recalcularTotalesOrden();
            }
        }
    });
});
