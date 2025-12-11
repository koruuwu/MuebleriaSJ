document.addEventListener("DOMContentLoaded", function () {
    const subtotalInput = document.querySelector("#id_subtotal");
    const isvInput = document.querySelector("#id_isv");
    const totalInput = document.querySelector("#id_total");

    // Hacer campos de solo lectura
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

        // Sumar subtotales de cada fila
        document.querySelectorAll('input[id$="-subtotal"]').forEach(input => {
            subtotalGeneral += parseFloat(input.value) || 0;
        });

        const descuentoInput = document.querySelector("#id_descuento");
        const isvInput = document.querySelector("#id_isv");
        const subtotalInput = document.querySelector("#id_subtotal");
        const totalInput = document.querySelector("#id_total");

        const descuentoPorcentaje = parseFloat(descuentoInput?.value) || 0;

        // Calcular el descuento como porcentaje
        const descuentoAplicado = subtotalGeneral * (descuentoPorcentaje / 100);

        const isv = subtotalGeneral * 0.15;
        const total = subtotalGeneral + isv - descuentoAplicado;

        if (subtotalInput) subtotalInput.value = subtotalGeneral.toFixed(2);
        if (isvInput) isvInput.value = isv.toFixed(2);
        if (totalInput) totalInput.value = total.toFixed(2);
        
        // Disparar evento para otros listeners
        if (totalInput) {
            totalInput.dispatchEvent(new Event('totalActualizado'));
        }
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

        if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) {
            console.warn("Campos faltantes en fila", { fila });
            return;
        }

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
                    if (!ct.includes("application/json")) {
                        return r.text().then(t => {
                            throw new Error("Respuesta no JSON: " + t);
                        });
                    }
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

        // Configurar eventos
        muebleSelect.addEventListener("change", handleSelectChange);
        cantidadInput.addEventListener("input", actualizarSubtotalFila);
        precioInput.addEventListener("input", actualizarSubtotalFila);

        // Inicializar subtotal si hay valores
        const cantidadVal = parseFloat(cantidadInput.value) || 0;
        const precioVal = parseFloat(precioInput.value) || 0;
        if (cantidadVal > 0 && precioVal > 0) {
            subtotalInput.value = (cantidadVal * precioVal).toFixed(2);
        }

        // Soporte para select2 si existe
        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(muebleSelect).on("select2:select select2:close change", function () {
                setTimeout(handleSelectChange, 10);
            });
        }
    }

    // Función para inicializar todos los cálculos
    function inicializarCalculos() {
        // Recalcular subtotales de cada fila existente
        document.querySelectorAll('[id^="detallesordene_set-"]').forEach(row => {
            const cantidadInput = row.querySelector('input[id$="-cantidad"]');
            const precioInput = row.querySelector('input[id$="-precio_unitario"]');
            const subtotalInput = row.querySelector('input[id$="-subtotal"]');
            
            if (cantidadInput && precioInput && subtotalInput) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const precio = parseFloat(precioInput.value) || 0;
                if (cantidad > 0 || precio > 0) {
                    subtotalInput.value = (cantidad * precio).toFixed(2);
                }
            }
        });
        
        // Recalcular totales generales
        recalcularTotalesOrden();
    }

    // Conectar filas existentes
    document.querySelectorAll('[id^="detallesordene_set-"][id$="-id_mueble"]').forEach(select => {
        const fila = select.closest('.form-row, .dynamic-detallesordene_set, .inline-related');
        conectarEventosFila(fila);
    });

    // Conectar filas nuevas dinámicamente creadas
    document.body.addEventListener("formset:added", function (event) {
        console.log("Formset añadido", event.target);
        setTimeout(() => {
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 50);
    });

    // Recalcular totales cuando cambie el descuento
    const descuentoInput = document.querySelector("#id_descuento");
    if (descuentoInput) {
        descuentoInput.addEventListener("input", recalcularTotalesOrden);
    }

    /* =====================================================
       ======== INICIALIZACIÓN AL CARGAR LA PÁGINA =========
       ===================================================== */

    // Ejecutar inicialización después de un breve delay para asegurar que el DOM esté listo
    setTimeout(() => {
        console.log("Inicializando cálculos...");
        inicializarCalculos();
        
        // Conectar todas las filas nuevamente (por si hay valores precargados)
        document.querySelectorAll('.form-row, .dynamic-detallesordene_set, .inline-related').forEach(fila => {
            const hasFields = fila.querySelector('select[id$="-id_mueble"]') || 
                             fila.querySelector('input[id$="-precio_unitario"]');
            if (hasFields) {
                conectarEventosFila(fila);
            }
        });
    }, 300);

    // También inicializar cuando la página termine de cargar completamente
    window.addEventListener('load', function() {
        console.log("Página cargada, recalculando...");
        setTimeout(inicializarCalculos, 200);
    });
});