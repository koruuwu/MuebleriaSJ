document.addEventListener("DOMContentLoaded", function () {
    /* ============================
       CONFIGURACIÓN GLOBAL
    ============================ */
    const CONFIG = {
        maxRetries: 3,
        retryDelay: 100
    };

    let isInitializing = false;
    let initializationAttempts = 0;

    /* ============================
       FUNCIONES DE UTILIDAD
    ============================ */
    function getAdminBaseUrl() {
        try {
            const parts = window.location.pathname.split("/").filter(Boolean);
            const adminIndex = parts.indexOf("admin");
            if (adminIndex === -1) return "/admin/";
            const baseParts = parts.slice(0, adminIndex + 3);
            return "/" + baseParts.join("/") + "/";
        } catch (error) {
            console.warn("Error al obtener base URL, usando default:", error);
            return "/admin/";
        }
    }

    const adminBase = getAdminBaseUrl();

    function safeParseFloat(value, defaultValue = 0) {
        if (value === null || value === undefined || value === "") return defaultValue;
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /* ============================
       MANEJO DE CAMPOS SOLO LECTURA
    ============================ */
    function setupReadOnlyFields() {
        const readOnlySelectors = [
            "#id_subtotal",
            "#id_isv",
            "#id_total",
            "input[id$='-subtotal']"
        ];

        readOnlySelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(field => {
                try {
                    field.readOnly = true;
                    // Añadir estilo visual para indicar que es solo lectura
                    field.style.backgroundColor = "#f5f5f5";
                    field.style.cursor = "not-allowed";
                } catch (error) {
                    console.warn(`No se pudo configurar campo ${selector}:`, error);
                }
            });
        });
    }

    /* ============================
       SISTEMA 1: ORDEN DE MUEBLES
    ============================ */
    function setupOrdenMuebles() {
        const subtotalInput = document.querySelector("#id_subtotal");
        const isvInput = document.querySelector("#id_isv");
        const totalInput = document.querySelector("#id_total");

        // Configurar campos como solo lectura
        [subtotalInput, isvInput, totalInput].forEach(input => {
            if (input) input.readOnly = true;
        });

        // Función principal para calcular totales de orden
        function recalcularTotalesOrden() {
            try {
                let subtotalGeneral = 0;
                
                // Sumar todos los subtotales de las filas
                document.querySelectorAll('input[id$="-subtotal"]').forEach(input => {
                    subtotalGeneral += safeParseFloat(input.value);
                });

                // Obtener descuento
                const descuentoInput = document.querySelector("#id_descuento");
                const descuentoPorcentaje = safeParseFloat(descuentoInput?.value);
                
                // Cálculos
                const descuentoAplicado = subtotalGeneral * (descuentoPorcentaje / 100);
                const isv = subtotalGeneral * 0.15;
                const total = subtotalGeneral + isv - descuentoAplicado;

                // Actualizar campos
                if (subtotalInput) subtotalInput.value = subtotalGeneral.toFixed(2);
                if (isvInput) isvInput.value = isv.toFixed(2);
                if (totalInput) {
                    totalInput.value = total.toFixed(2);
                    // Disparar evento personalizado para otros listeners
                    totalInput.dispatchEvent(new Event('totalActualizado'));
                }

                return true;
            } catch (error) {
                console.error("Error en recalcularTotalesOrden:", error);
                return false;
            }
        }

        // Configurar eventos para una fila de muebles
        function conectarEventosFilaMueble(fila) {
            if (!fila) return;

            const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
            const precioInput = fila.querySelector('input[id$="-precio_unitario"]');
            const cantidadInput = fila.querySelector('input[id$="-cantidad"]');
            const subtotalInput = fila.querySelector('input[id$="-subtotal"]');

            if (!muebleSelect || !precioInput || !cantidadInput || !subtotalInput) return;

            // Configurar campos como solo lectura
            if (subtotalInput) subtotalInput.readOnly = true;
            if (precioInput) precioInput.readOnly = true;

            // Función para manejar cambio de mueble
            async function handleSelectChange() {
                const muebleId = muebleSelect.value;

                if (!muebleId) {
                    precioInput.value = "";
                    actualizarSubtotalFila();
                    return;
                }

                try {
                    const response = await fetch(`${adminBase}obtener_precio_mueble/${muebleId}/`);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    
                    const data = await response.json();
                    precioInput.value = data.precio;
                    actualizarSubtotalFila();

                    // Compatibilidad con select2 si existe
                    if (window.jQuery && window.jQuery.fn.select2) {
                        window.jQuery(muebleSelect).trigger('change.select2');
                    }
                } catch (error) {
                    console.error("Error obteniendo precio del mueble:", error);
                    precioInput.value = "0";
                    actualizarSubtotalFila();
                }
            }

            // Función para actualizar subtotal de fila
            function actualizarSubtotalFila() {
                try {
                    const cantidad = safeParseFloat(cantidadInput.value);
                    const precio = safeParseFloat(precioInput.value);
                    const subtotal = cantidad * precio;

                    subtotalInput.value = subtotal.toFixed(2);
                    recalcularTotalesOrden();
                } catch (error) {
                    console.error("Error en actualizarSubtotalFila:", error);
                }
            }

            // Configurar event listeners con debounce
            muebleSelect.addEventListener("change", handleSelectChange);
            cantidadInput.addEventListener("input", debounce(actualizarSubtotalFila, 300));
            
            // Precio input debería ser de solo lectura, pero por si acaso
            precioInput.addEventListener("input", debounce(actualizarSubtotalFila, 300));

            // Inicializar valores si ya existen
            const cantidad = safeParseFloat(cantidadInput.value);
            const precio = safeParseFloat(precioInput.value);

            if (cantidad > 0 && precio > 0) {
                subtotalInput.value = (cantidad * precio).toFixed(2);
                actualizarSubtotalFila();
            }

            // Configurar select2 si está disponible
            if (window.jQuery && window.jQuery.fn.select2) {
                // Limpiar eventos duplicados
                window.jQuery(muebleSelect).off('select2:select');
                
                // Configurar evento seguro
                window.jQuery(muebleSelect).on('select2:select', function () {
                    setTimeout(handleSelectChange, 50);
                });
            }

            return true;
        }

        // Configurar todas las filas de muebles
        function conectarTodasLasFilasMuebles() {
            document.querySelectorAll('select[id$="-id_mueble"]').forEach(select => {
                const fila = select.closest('.form-row, .dynamic-detallecotizaciones_set, .inline-related, tr');
                if (fila) conectarEventosFilaMueble(fila);
            });
            
            // Configurar evento de descuento
            const descuentoInput = document.querySelector("#id_descuento");
            if (descuentoInput) {
                descuentoInput.addEventListener("input", debounce(recalcularTotalesOrden, 300));
            }
        }

        // Inicializar cálculos de muebles
        function inicializarCalculosMuebles() {
            try {
                document.querySelectorAll('[id^="detalleCotizaciones_set-"]').forEach(row => {
                    const cantidadInput = row.querySelector('input[id$="-cantidad"]');
                    const precioInput = row.querySelector('input[id$="-precio_unitario"]');
                    const subtotalInput = row.querySelector('input[id$="-subtotal"]');

                    if (cantidadInput && precioInput && subtotalInput) {
                        const cantidad = safeParseFloat(cantidadInput.value);
                        const precio = safeParseFloat(precioInput.value);

                        if (cantidad > 0 && precio > 0) {
                            subtotalInput.value = (cantidad * precio).toFixed(2);
                        }
                    }
                });

                recalcularTotalesOrden();
                return true;
            } catch (error) {
                console.error("Error en inicializarCalculosMuebles:", error);
                return false;
            }
        }

        return {
            conectarEventosFilaMueble,
            conectarTodasLasFilasMuebles,
            inicializarCalculosMuebles,
            recalcularTotalesOrden
        };
    }

    /* ============================
       SISTEMA 2: REQUERIMIENTO DE MATERIALES
    ============================ */
    function setupRequerimientoMateriales() {
        // Configurar eventos para una fila de materiales
        function conectarFilaRequerimiento(fila) {
            if (!fila) return;

            const materialSelect = fila.querySelector('select[id$="-material"]');
            const proveedorSelect = fila.querySelector('select[id$="-proveedor"]');
            const precioInput = fila.querySelector('input[id$="-precio_actual"]');
            const cantidadInput = fila.querySelector('input[id$="-cantidad_necesaria"]');
            const subtotalInput = fila.querySelector('input[id$="-subtotal"]');

            if (!materialSelect || !proveedorSelect || !precioInput || !cantidadInput || !subtotalInput) {
                console.warn("Campos faltantes en fila de materiales:", fila);
                return false;
            }

            // Configurar campo subtotal como solo lectura
            if (subtotalInput) {
                subtotalInput.readOnly = true;
                subtotalInput.style.backgroundColor = "#f5f5f5";
            }

            // Función para actualizar precio basado en material y proveedor
            async function actualizarPrecio() {
                const materialId = materialSelect.value;
                const proveedorId = proveedorSelect.value;

                if (!materialId || !proveedorId) {
                    precioInput.value = "0";
                    recalcularSubtotal();
                    return;
                }

                try {
                    const response = await fetch(
                        `${adminBase}obtener_precio_material/${materialId}/${proveedorId}/`
                    );
                    
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    
                    const data = await response.json();
                    precioInput.value = data.precio || "0";
                    recalcularSubtotal();
                } catch (error) {
                    console.error("Error al obtener precio del material:", error);
                    precioInput.value = "0";
                    recalcularSubtotal();
                }
            }

            // Función para recalcular subtotal
            function recalcularSubtotal() {
                try {
                    const cant = safeParseFloat(cantidadInput.value);
                    const precio = safeParseFloat(precioInput.value);
                    subtotalInput.value = (cant * precio).toFixed(2);
                } catch (error) {
                    console.error("Error en recalcularSubtotal:", error);
                    subtotalInput.value = "0.00";
                }
            }

            // Configurar event listeners
            materialSelect.addEventListener("change", actualizarPrecio);
            proveedorSelect.addEventListener("change", actualizarPrecio);
            cantidadInput.addEventListener("input", debounce(recalcularSubtotal, 300));
            precioInput.addEventListener("input", debounce(recalcularSubtotal, 300));

            // Compatibilidad con select2
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery(materialSelect).on(
                    "select2:select select2:close change", 
                    debounce(actualizarPrecio, 100)
                );
                window.jQuery(proveedorSelect).on(
                    "select2:select select2:close change", 
                    debounce(actualizarPrecio, 100)
                );
            }

            // Inicializar si ya hay valores
            const materialId = materialSelect.value;
            const proveedorId = proveedorSelect.value;
            const cantidad = safeParseFloat(cantidadInput.value);
            const precio = safeParseFloat(precioInput.value);

            if (materialId && proveedorId && cantidad > 0 && precio > 0) {
                subtotalInput.value = (cantidad * precio).toFixed(2);
            } else if (materialId && proveedorId) {
                actualizarPrecio();
            }

            return true;
        }

        // Conectar todas las filas existentes de materiales
        function conectarTodasLasFilasMateriales() {
            document.querySelectorAll('[id^="requerimientomateriale_set-"][id$="-material"]')
                .forEach(select => {
                    const fila = select.closest('.inline-related, .form-row, tr, .dynamic-form');
                    if (fila) conectarFilaRequerimiento(fila);
                });
        }

        return {
            conectarFilaRequerimiento,
            conectarTodasLasFilasMateriales
        };
    }

    /* ============================
       MANEJO DE FORMULARIOS DINÁMICOS
    ============================ */
    function setupFormsetHandlers(mueblesSystem, materialesSystem) {
        // Escuchar eventos de Django admin para nuevas filas
        document.body.addEventListener("formset:added", function (event) {
            setTimeout(() => {
                const fila = event.target;
                
                // Determinar qué tipo de fila es
                if (fila.querySelector('select[id$="-id_mueble"]')) {
                    mueblesSystem.conectarEventosFilaMueble(fila);
                    mueblesSystem.inicializarCalculosMuebles();
                } else if (fila.querySelector('select[id$="-material"]')) {
                    materialesSystem.conectarFilaRequerimiento(fila);
                }
            }, 150);
        });

        // Escuchar eventos de Django admin alternativos
        document.addEventListener("django:formset:added", function(event) {
            setTimeout(() => {
                const fila = event.target;
                
                if (fila.querySelector('select[id$="-id_mueble"]')) {
                    mueblesSystem.conectarEventosFilaMueble(fila);
                    mueblesSystem.inicializarCalculosMuebles();
                } else if (fila.querySelector('select[id$="-material"]')) {
                    materialesSystem.conectarFilaRequerimiento(fila);
                }
            }, 150);
        });

        // Listener global como respaldo
        document.addEventListener('input', function(event) {
            const target = event.target;
            
            if (target.matches('input[id$="-cantidad"], input[id$="-precio_unitario"], input[id$="-precio_actual"], input[id$="-cantidad_necesaria"]')) {
                const fila = target.closest('.form-row, .dynamic-form, .inline-related, tr');
                if (!fila) return;

                const subtotalInput = fila.querySelector('input[id$="-subtotal"]');
                const cantidadInput = fila.querySelector('input[id$="-cantidad"], input[id$="-cantidad_necesaria"]');
                const precioInput = fila.querySelector('input[id$="-precio_unitario"], input[id$="-precio_actual"]');

                if (subtotalInput && cantidadInput && precioInput) {
                    const cantidad = safeParseFloat(cantidadInput.value);
                    const precio = safeParseFloat(precioInput.value);
                    subtotalInput.value = (cantidad * precio).toFixed(2);
                    
                    // Recalcular totales si es sistema de muebles
                    const muebleSelect = fila.querySelector('select[id$="-id_mueble"]');
                    if (muebleSelect && window.mueblesSystem) {
                        window.mueblesSystem.recalcularTotalesOrden();
                    }
                }
            }
        });
    }

    /* ============================
       INICIALIZACIÓN PRINCIPAL
    ============================ */
    function initializeAllSystems() {
        if (isInitializing) return;
        
        isInitializing = true;
        initializationAttempts++;
        
        console.log(`Inicializando sistemas (intento ${initializationAttempts})...`);
        
        try {
            // Configurar campos de solo lectura
            setupReadOnlyFields();
            
            // Inicializar ambos sistemas
            const mueblesSystem = setupOrdenMuebles();
            const materialesSystem = setupRequerimientoMateriales();
            
            // Guardar referencia global para acceso desde event listeners
            window.mueblesSystem = mueblesSystem;
            
            // Configurar handlers para formularios dinámicos
            setupFormsetHandlers(mueblesSystem, materialesSystem);
            
            // Conectar todas las filas existentes
            mueblesSystem.conectarTodasLasFilasMuebles();
            materialesSystem.conectarTodasLasFilasMateriales();
            
            // Inicializar cálculos
            mueblesSystem.inicializarCalculosMuebles();
            
            console.log("Sistemas inicializados correctamente");
            isInitializing = false;
            initializationAttempts = 0;
            return true;
            
        } catch (error) {
            console.error("Error en la inicialización:", error);
            isInitializing = false;
            
            // Reintentar si no hemos superado el máximo
            if (initializationAttempts < CONFIG.maxRetries) {
                console.log(`Reintentando en ${CONFIG.retryDelay}ms...`);
                setTimeout(initializeAllSystems, CONFIG.retryDelay);
            } else {
                console.error("Máximo de reintentos alcanzado");
            }
            return false;
        }
    }

    /* ============================
       EVENTOS DE CARGA Y RECARGA
    ============================ */
    // Inicializar inmediatamente
    setTimeout(initializeAllSystems, 100);
    
    // Inicializar cuando la página termine de cargar
    window.addEventListener('load', function() {
        setTimeout(initializeAllSystems, 200);
    });
    
    // Manejar navegación hacia atrás/delante (cache del navegador)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            setTimeout(initializeAllSystems, 300);
        }
    });
    
    // Inicializar cuando cambie la visibilidad de la pestaña
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            setTimeout(initializeAllSystems, 100);
        }
    });

    /* ============================
       EXPORTAR FUNCIONES PARA DEBUG
    ============================ */
    window.debugRecalcularTotales = function() {
        if (window.mueblesSystem && window.mueblesSystem.recalcularTotalesOrden) {
            window.mueblesSystem.recalcularTotalesOrden();
            console.log("Totales recalculados manualmente");
        }
    };
});