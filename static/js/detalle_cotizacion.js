console.log("hola - Script cargado");

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOMContentLoaded ejecutado");
    
    const subtotalInput = document.querySelector("#id_subtotal");
    const isvInput = document.querySelector("#id_isv");
    const totalInput = document.querySelector("#id_total");

    // Hacer campos de solo lectura
    if (subtotalInput) {
        subtotalInput.readOnly = true;
        console.log("Subtotal input encontrado");
    }
    if (isvInput) {
        isvInput.readOnly = true;
        console.log("ISV input encontrado");
    }
    if (totalInput) {
        totalInput.readOnly = true;
        console.log("Total input encontrado");
    }

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
        console.log("recalcularTotalesOrden llamado");
        let subtotalGeneral = 0;

        // Sumar subtotales de cada fila
        document.querySelectorAll('input[id$="-subtotal"]').forEach(input => {
            const valor = parseFloat(input.value) || 0;
            subtotalGeneral += valor;
            console.log(`Subtotal fila: ${input.id} = ${valor}`);
        });

        const descuentoInput = document.querySelector("#id_descuento");
        const isvInput = document.querySelector("#id_isv");
        const subtotalInput = document.querySelector("#id_subtotal");
        const totalInput = document.querySelector("#id_total");

        const descuentoPorcentaje = parseFloat(descuentoInput?.value) || 0;
        console.log(`Descuento: ${descuentoPorcentaje}%`);

        // Calcular el descuento como porcentaje
        const descuentoAplicado = subtotalGeneral * (descuentoPorcentaje / 100);

        const isv = subtotalGeneral * 0.15;
        const total = subtotalGeneral + isv - descuentoAplicado;

        console.log(`Cálculos: Subtotal=${subtotalGeneral.toFixed(2)}, ISV=${isv.toFixed(2)}, Descuento=${descuentoAplicado.toFixed(2)}, Total=${total.toFixed(2)}`);

        if (subtotalInput) {
            subtotalInput.value = subtotalGeneral.toFixed(2);
            console.log("Subtotal actualizado:", subtotalInput.value);
        }
        if (isvInput) {
            isvInput.value = isv.toFixed(2);
            console.log("ISV actualizado:", isvInput.value);
        }
        if (totalInput) {
            totalInput.value = total.toFixed(2);
            console.log("Total actualizado:", totalInput.value);
            // Disparar evento para otros listeners
            totalInput.dispatchEvent(new Event('totalActualizado'));
        }
    }   

    /* =====================================================
       ======= EVENTOS Y CÁLCULO DE CADA FILA DETALLE ======
       ===================================================== */

    function conectarEventosFila(fila) {
        if (!fila) {
            console.log("Fila nula en conectarEventosFila");
            return;
        }

        console.log("Conectando eventos para fila:", fila);

        const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
        const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
        const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
        const subtotalInput = fila.querySelector('input[id$="-subtotal"]');

        console.log("Elementos encontrados en fila:", {
            muebleSelect: !!muebleSelect,
            precioInput: !!precioInput,
            cantidadInput: !!cantidadInput,
            subtotalInput: !!subtotalInput
        });

        if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) {
            console.warn("Campos faltantes en fila", { fila });
            return;
        }

        // Remover eventos previos para evitar duplicados
        muebleSelect.removeEventListener("change", handleSelectChange);
        cantidadInput.removeEventListener("input", actualizarSubtotalFila);
        precioInput.removeEventListener("input", actualizarSubtotalFila);

        function handleSelectChange() {
            console.log("handleSelectChange llamado para mueble:", muebleSelect.value);
            const muebleId = muebleSelect.value;
            if (!muebleId) {
                precioInput.value = "";
                actualizarSubtotalFila();
                return;
            }

            console.log("Fetching precio para mueble ID:", muebleId);
            fetch(`${adminBase}/obtener_precio_mueble/${muebleId}/`)
                .then(r => {
                    const ct = r.headers.get("content-type") || "";
                    if (!ct.includes("application/json")) {
                        return r.text().then(t => {
                            console.error("Respuesta no JSON:", t);
                            throw new Error("Respuesta no JSON: " + t);
                        });
                    }
                    return r.json();
                })
                .then(data => {
                    console.log("Datos recibidos:", data);
                    if (data.precio !== undefined) {
                        precioInput.value = data.precio;
                        console.log("Precio actualizado:", data.precio);
                        actualizarSubtotalFila();
                    }
                })
                .catch(err => console.error("Error AJAX precio:", err));
        }

        function actualizarSubtotalFila() {
            const cantidad = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;
            const subtotal = cantidad * precio;
            
            console.log(`Actualizando subtotal: ${cantidad} × ${precio} = ${subtotal}`);
            
            subtotalInput.value = subtotal.toFixed(2);
            console.log("Subtotal fila actualizado:", subtotalInput.value);
            
            recalcularTotalesOrden();
        }

        // Configurar eventos
        muebleSelect.addEventListener("change", handleSelectChange);
        cantidadInput.addEventListener("input", actualizarSubtotalFila);
        precioInput.addEventListener("input", actualizarSubtotalFila);

        // Inicializar subtotal si hay valores
        const cantidadVal = parseFloat(cantidadInput.value) || 0;
        const precioVal = parseFloat(precioInput.value) || 0;
        console.log(`Valores iniciales: cantidad=${cantidadVal}, precio=${precioVal}`);
        
        if (cantidadVal > 0 && precioVal > 0) {
            subtotalInput.value = (cantidadVal * precioVal).toFixed(2);
            console.log("Subtotal inicial calculado:", subtotalInput.value);
        } else if (subtotalInput.value && parseFloat(subtotalInput.value) > 0) {
            // Si ya tiene valor, asegurar que esté bien formateado
            subtotalInput.value = parseFloat(subtotalInput.value).toFixed(2);
        }

        // Trigger para calcular si hay valores
        if (cantidadVal > 0 || precioVal > 0 || subtotalInput.value) {
            setTimeout(() => {
                actualizarSubtotalFila();
            }, 100);
        }

        // Soporte para select2 si existe
        if (window.jQuery && window.jQuery.fn.select2 && muebleSelect) {
            console.log("Select2 detectado, configurando eventos");
            window.jQuery(muebleSelect).off('select2:select select2:close change');
            window.jQuery(muebleSelect).on("select2:select select2:close change", function () {
                console.log("Evento Select2 disparado");
                setTimeout(handleSelectChange, 10);
            });
        }
        
        console.log("Eventos conectados para fila");
    }

    // Función para inicializar todos los cálculos
    function inicializarCalculos() {
        console.log("=== INICIALIZAR CÁLCULOS ===");
        
        // Recalcular subtotales de cada fila existente
        let filasProcesadas = 0;
        document.querySelectorAll('[id^="detalleCotizaciones_set-"]').forEach(row => {
            console.log("Procesando fila:", row);
            const cantidadInput = row.querySelector('input[id$="-cantidad"]');
            const precioInput = row.querySelector('input[id$="-precio_unitario"]');
            const subtotalInput = row.querySelector('input[id$="-subtotal"]');
            
            if (cantidadInput && precioInput && subtotalInput) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const precio = parseFloat(precioInput.value) || 0;
                console.log(`Valores fila: cantidad=${cantidad}, precio=${precio}`);
                
                if (cantidad > 0 && precio > 0) {
                    subtotalInput.value = (cantidad * precio).toFixed(2);
                    console.log(`Subtotal calculado para ${subtotalInput.id}: ${subtotalInput.value}`);
                    filasProcesadas++;
                } else if (subtotalInput.value && parseFloat(subtotalInput.value) > 0) {
                    // Si ya tiene valor, asegurar formato
                    subtotalInput.value = parseFloat(subtotalInput.value).toFixed(2);
                    filasProcesadas++;
                }
            }
        });
        
        console.log(`Filas procesadas: ${filasProcesadas}`);
        
        // Recalcular totales generales
        recalcularTotalesOrden();
    }

    // Función para conectar todas las filas existentes
    function conectarTodasLasFilas() {
        console.log("=== CONECTANDO TODAS LAS FILAS ===");
        
        // Buscar por múltiples selectores posibles
        const selectors = [
            'select[id$="-id_mueble"]',
            '[id^="detalleCotizaciones_set-"][id$="-id_mueble"]'
        ];
        
        let filasConectadas = 0;
        
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(select => {
                const fila = select.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr');
                if (fila) {
                    conectarEventosFila(fila);
                    filasConectadas++;
                    console.log(`Fila conectada usando selector: ${selector}`);
                }
            });
        });
        
        console.log(`Total filas conectadas: ${filasConectadas}`);
        
        // Si no encontramos filas, intentar otra estrategia
        if (filasConectadas === 0) {
            console.log("Buscando filas alternativamente...");
            document.querySelectorAll('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr').forEach(fila => {
                const hasFields = fila.querySelector('select[id$="-id_mueble"]') || 
                                 fila.querySelector('input[id$="-precio_unitario"]');
                if (hasFields) {
                    conectarEventosFila(fila);
                    filasConectadas++;
                }
            });
            console.log(`Filas conectadas (alternativa): ${filasConectadas}`);
        }
    }

    // Conectar filas nuevas dinámicamente creadas
    document.body.addEventListener("formset:added", function (event) {
        console.log("Evento formset:added disparado", event.target);
        setTimeout(() => {
            console.log("Conectando fila añadida después de delay");
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 100);
    });

    // También manejar otros eventos de formularios dinámicos
    document.addEventListener('django:formset:added', function(event) {
        console.log("Evento django:formset:added disparado", event.target);
        setTimeout(() => {
            conectarEventosFila(event.target);
            inicializarCalculos();
        }, 100);
    });

    // Recalcular totales cuando cambie el descuento
    const descuentoInput = document.querySelector("#id_descuento");
    if (descuentoInput) {
        console.log("Descuento input encontrado, conectando evento");
        descuentoInput.addEventListener("input", recalcularTotalesOrden);
    }

    /* =====================================================
       ======== INICIALIZACIÓN AL CARGAR LA PÁGINA =========
       ===================================================== */

    // Función de inicialización completa
    function inicializarCompleta() {
        console.log("=== INICIALIZACIÓN COMPLETA ===");
        
        // Paso 1: Conectar todas las filas
        conectarTodasLasFilas();
        
        // Paso 2: Inicializar cálculos
        setTimeout(() => {
            inicializarCalculos();
        }, 200);
        
        // Paso 3: Forzar recálculo después de más tiempo
        setTimeout(() => {
            console.log("Recálculo final después de 500ms");
            recalcularTotalesOrden();
        }, 500);
    }

    // Ejecutar inicialización después de un breve delay
    setTimeout(() => {
        console.log("Inicialización programada (300ms)");
        inicializarCompleta();
    }, 300);

    // También inicializar cuando la página termine de cargar completamente
    window.addEventListener('load', function() {
        console.log("Evento load disparado");
        setTimeout(() => {
            console.log("Inicialización desde load (200ms)");
            inicializarCompleta();
        }, 200);
    });

    // Manejar también cuando se vuelve a una página desde cache
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            console.log("Página cargada desde cache (pageshow)");
            setTimeout(() => {
                inicializarCompleta();
            }, 300);
        }
    });

    // Conectar eventos a los inputs de cantidad y precio globalmente como respaldo
    document.addEventListener('input', function(event) {
        const target = event.target;
        if (target && (target.matches('input[id$="-cantidad"]') || target.matches('input[id$="-precio_unitario"]'))) {
            console.log("Evento input global capturado:", target.id);
            const fila = target.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr');
            if (fila) {
                const subtotalInput = fila.querySelector('input[id$="-subtotal"]');
                const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
                const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
                
                if (subtotalInput && cantidadInput && precioInput) {
                    const cantidad = parseFloat(cantidadInput.value) || 0;
                    const precio = parseFloat(precioInput.value) || 0;
                    subtotalInput.value = (cantidad * precio).toFixed(2);
                    recalcularTotalesOrden();
                }
            }
        }
    });

    console.log("Script completamente cargado y configurado");
});