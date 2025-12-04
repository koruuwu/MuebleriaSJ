document.addEventListener("DOMContentLoaded", function() {
    console.log('Script de estado de inventario de MUEBLES cargado');

    // Mapeo de estados a IDs - Ajustar según tu tabla de Estados
    const ESTADOS_IDS = {
        'Disponible': 1,
        'Bajo Stock': 2,
        'Agotado': 3,
        'Descontinuado': 4
    };

    // Configurar listeners para cantidad disponible
    function setupCantidadDisponibleListeners() {
        const cantidadInputs = document.querySelectorAll('input[id$="-cantidad_disponible"], input[name="cantidad_disponible"]');
        
        cantidadInputs.forEach(input => {
            input.removeEventListener('input', handleCantidadChange);
            input.removeEventListener('change', handleCantidadChange);

            input.addEventListener('input', handleCantidadChange);
            input.addEventListener('change', handleCantidadChange);

            actualizarEstadoDesdeCantidad(input);
        });
    }

    function handleCantidadChange(event) {
        actualizarEstadoDesdeCantidad(this);
    }

    function actualizarEstadoDesdeCantidad(input) {
        const cantidad = parseInt(input.value) || 0;
        console.log(`Actualizando estado para cantidad: ${cantidad}`);

        // Campo estado
        const estadoField = document.querySelector('select[id$="-estado"], select[name="estado"]');
        if (!estadoField) return;

        // Obtener el mueble relacionado
        const muebleId = obtenerMuebleId();
        if (!muebleId) {
            aplicarEstado(estadoField, calcularEstado(cantidad, 10, false));
            return;
        }

        obtenerInfoMueble(muebleId, function(muebleInfo) {
            if (muebleInfo) {
                const nuevoEstado = calcularEstado(cantidad, muebleInfo.stock_minimo, muebleInfo.Descontinuado);
                aplicarEstado(estadoField, nuevoEstado);
            } else {
                aplicarEstado(estadoField, calcularEstado(cantidad, 10, false));
            }
        });
    }

    function obtenerMuebleId() {
        const muebleSelect = document.querySelector('select[id$="-id_mueble"], select[name="id_mueble"]');
        return muebleSelect && muebleSelect.value ? muebleSelect.value : null;
    }

    function obtenerInfoMueble(muebleId, callback) {
        const url = `/admin/Compras/inventariomueble/obtener_info_mueble/${muebleId}/`;
        fetch(url)
        .then(resp => resp.ok ? resp.json() : Promise.reject('Error en respuesta'))
        .then(data => callback(data))
        .catch(err => {
            console.error('Error al obtener info del mueble:', err);
            callback({ stock_minimo: 10, Descontinuado: false });
        });
    }

    function calcularEstado(cantidad, stockMinimo, descontinuado) {
        if (descontinuado) return 'Descontinuado';
        if (cantidad <= 0) return 'Agotado';
        if (cantidad < stockMinimo) return 'Bajo Stock';
        return 'Disponible';
    }

    function aplicarEstado(estadoField, nuevoEstado) {
        const estadoId = ESTADOS_IDS[nuevoEstado];
        if (!estadoId) return;

        if (estadoField.value != estadoId) {
            estadoField.value = estadoId;
            estadoField.dispatchEvent(new Event('change', { bubbles: true }));
            estadoField.dispatchEvent(new Event('input', { bubbles: true }));
            console.log(`Estado actualizado: ${nuevoEstado} (ID: ${estadoId})`);
        }
    }

    function setupMutationObserver() {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1 && node.querySelector) {
                        if (node.querySelector('input[id$="-cantidad_disponible"], input[name="cantidad_disponible"]')) {
                            setTimeout(setupCantidadDisponibleListeners, 100);
                        }
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    function initialize() {
        if (window.location.pathname.includes('/inventariomueble/')) {
            setTimeout(() => {
                setupCantidadDisponibleListeners();
                setupMutationObserver();
                // Escuchar cambios en el mueble
                const muebleSelects = document.querySelectorAll('select[id$="-id_mueble"]');
                muebleSelects.forEach(select => {
                    select.addEventListener('change', () => {
                        setTimeout(setupCantidadDisponibleListeners, 100);
                    });
                });
            }, 500);
        }
    }

    initialize();
});
