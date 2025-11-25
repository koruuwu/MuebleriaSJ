document.addEventListener("DOMContentLoaded", function() {
    console.log('Script de estado de inventario cargado - VERSIÓN MEJORADA');
    
    // Mapeo de estados a IDs - USANDO TUS IDs EXISTENTES
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
            // Remover listeners existentes para evitar duplicados
            input.removeEventListener('input', handleCantidadChange);
            input.removeEventListener('change', handleCantidadChange);
            
            // Agregar nuevos listeners
            input.addEventListener('input', handleCantidadChange);
            input.addEventListener('change', handleCantidadChange);
            
            // Actualizar estado inicial
            actualizarEstadoDesdeCantidad(input);
        });
    }
    
    // Handler para cambios en cantidad
    function handleCantidadChange(event) {
        actualizarEstadoDesdeCantidad(this);
    }
    
    // Función principal para actualizar el estado desde cantidad
    function actualizarEstadoDesdeCantidad(input) {
        const cantidad = parseInt(input.value) || 0;
        
        console.log(`Actualizando estado para cantidad: ${cantidad}`);
        
        // Obtener el campo de estado
        const estadoField = document.querySelector('select[id$="-estado"], select[name="estado"]');
        
        if (!estadoField) {
            console.log('No se encontró el campo estado');
            return;
        }
        
        // Obtener información del material
        const materialId = obtenerMaterialId();
        if (!materialId) {
            console.log('No se pudo obtener el ID del material');
            // Usar valores por defecto
            const nuevoEstado = calcularEstado(cantidad, 10, false);
            aplicarEstado(estadoField, nuevoEstado);
            return;
        }
        
        // Obtener información del material via AJAX
        obtenerInfoMaterial(materialId, function(materialInfo) {
            if (materialInfo) {
                const nuevoEstado = calcularEstado(cantidad, materialInfo.stock_minimo, materialInfo.descontinuado);
                aplicarEstado(estadoField, nuevoEstado);
            } else {
                // Fallback con valores por defecto
                const nuevoEstado = calcularEstado(cantidad, 10, false);
                aplicarEstado(estadoField, nuevoEstado);
            }
        });
    }
    
    // Obtener el ID del material del formulario
    function obtenerMaterialId() {
        // Buscar select de material en formulario principal
        const materialSelect = document.querySelector('select[id$="-id_material"], select[name="id_material"]');
        if (materialSelect && materialSelect.value) {
            return materialSelect.value;
        }
        
        // Buscar en inlines (para DetalleRecibido)
        const inlineMaterialSelects = document.querySelectorAll('select[id$="-product"]');
        for (let select of inlineMaterialSelects) {
            if (select.value) {
                return select.value;
            }
        }
        
        return null;
    }
    
    // Obtener información del material via AJAX
    function obtenerInfoMaterial(materialId, callback) {
        const url = `/admin/Compras/inventariomateriale/obtener_info_material/${materialId}/`;
        
        fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta');
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error al obtener info del material:', error);
            // Valores por defecto si falla
            callback({
                stock_minimo: 10,
                descontinuado: false
            });
        });
    }
    
    // Calcular el estado basado en la cantidad y stock mínimo
    function calcularEstado(cantidad, stockMinimo, descontinuado) {
        if (descontinuado) {
            return 'Descontinuado';
        }
        
        if (cantidad <= 0) {
            return 'Agotado';
        } else if (cantidad < stockMinimo) {
            return 'Bajo Stock';
        } else {
            return 'Disponible';
        }
    }
    
    // Aplicar el estado al campo select
    function aplicarEstado(estadoField, nuevoEstado) {
        const estadoId = ESTADOS_IDS[nuevoEstado];
        
        if (!estadoId) {
            console.error(`ID no encontrado para estado: ${nuevoEstado}`);
            return;
        }

        // Solo actualizar si el valor es diferente
        if (estadoField.value != estadoId) {
            estadoField.value = estadoId;

            // Disparar eventos de cambio
            estadoField.dispatchEvent(new Event('change', { bubbles: true }));
            estadoField.dispatchEvent(new Event('input', { bubbles: true }));

            console.log(`Estado actualizado: ${nuevoEstado} (ID: ${estadoId})`);
        }
    }
    
    // Observar cambios en el DOM para detectar nuevos campos
    function setupMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            // Verificar si se agregaron campos de cantidad
                            if (node.querySelector && (
                                node.querySelector('input[id$="-cantidad_disponible"]') ||
                                node.querySelector('input[name="cantidad_disponible"]') ||
                                node.querySelector('input[id$="-aporte"]')
                            )) {
                                setTimeout(() => {
                                    setupCantidadDisponibleListeners();
                                    setupAporteListeners();
                                }, 100);
                            }
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // Configurar listeners para el campo APORTE (en DetalleRecibido)
    function setupAporteListeners() {
        const aporteInputs = document.querySelectorAll('input[id$="-aporte"]');
        
        aporteInputs.forEach(input => {
            // Remover listeners existentes
            input.removeEventListener('input', handleAporteChange);
            input.removeEventListener('change', handleAporteChange);
            
            // Agregar nuevos listeners
            input.addEventListener('input', handleAporteChange);
            input.addEventListener('change', handleAporteChange);
        });
    }
    
    // Handler para cambios en APORTE
    function handleAporteChange(event) {
        const aporte = parseInt(this.value) || 0;
        console.log(`Aporte cambiado: ${aporte}`);
        
        // Buscar el inventario relacionado y actualizar su estado
        actualizarEstadoDesdeAporte(this, aporte);
    }
    
    // Actualizar estado basado en APORTE
    function actualizarEstadoDesdeAporte(aporteInput, aporte) {
        const prefix = aporteInput.id.split('-aporte')[0];
        const productSelect = document.querySelector(`#${prefix}-product`);
        
        if (!productSelect || !productSelect.value) {
            console.log('No se encontró producto relacionado al aporte');
            return;
        }
        
        const materialId = productSelect.value;
        
        // Obtener información del material
        obtenerInfoMaterial(materialId, function(materialInfo) {
            if (materialInfo) {
                // Buscar el inventario existente para este material
                buscarInventarioMaterial(materialId, function(inventarioExistente) {
                    if (inventarioExistente) {
                        const nuevaCantidadTotal = (inventarioExistente.cantidad_disponible || 0) + aporte;
                        const nuevoEstado = calcularEstado(nuevaCantidadTotal, materialInfo.stock_minimo, materialInfo.descontinuado);
                        
                        console.log(`Estado proyectado: ${nuevoEstado} (Cantidad: ${nuevaCantidadTotal})`);
                        
                        // Aquí podrías mostrar una notificación o actualizar un campo visual
                        mostrarEstadoProyectado(nuevoEstado, prefix);
                    }
                });
            }
        });
    }
    
    // Buscar inventario existente para un material
    function buscarInventarioMaterial(materialId, callback) {
        // Esta función necesitaría una API endpoint para buscar el inventario
        // Por ahora usamos un valor por defecto
        callback({
            cantidad_disponible: 0
        });
    }
    
    // Mostrar estado proyectado (opcional - para feedback visual)
    function mostrarEstadoProyectado(estado, prefix) {
        // Puedes implementar notificaciones visuales aquí
        console.log(`Estado proyectado para ${prefix}: ${estado}`);
    }
    
    // Inicializar
    function initialize() {
        if (window.location.pathname.includes('/inventariomateriale/') || 
            window.location.pathname.includes('/listacompra/')) {
            
            setTimeout(() => {
                setupCantidadDisponibleListeners();
                setupAporteListeners();
                setupMutationObserver();
                
                // También escuchar cambios en el material
                const materialSelects = document.querySelectorAll('select[id$="-id_material"], select[id$="-product"]');
                materialSelects.forEach(select => {
                    select.addEventListener('change', function() {
                        setTimeout(() => {
                            setupCantidadDisponibleListeners();
                            setupAporteListeners();
                        }, 100);
                    });
                });
            }, 500);
        }
    }
    
    // Ejecutar inicialización
    initialize();
});