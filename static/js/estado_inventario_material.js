// js/inventario_material_estado.js
document.addEventListener("DOMContentLoaded", function() {
    console.log('Script de estado de inventario cargado');
    
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
            input.addEventListener('input', function() {
                actualizarEstadoInventario(this);
            });
            
            input.addEventListener('change', function() {
                actualizarEstadoInventario(this);
            });
            
            // Actualizar estado inicial
            actualizarEstadoInventario(input);
        });
    }
    
    // Función principal para actualizar el estado
    function actualizarEstadoInventario(input) {
        const cantidad = parseInt(input.value) || 0;
        const prefix = getFieldPrefix(input);
        
        console.log(`Actualizando estado para cantidad: ${cantidad}`);
        
        // Obtener el campo de estado - BUSCANDO EL SELECT CORRECTO
        const estadoField = document.querySelector(`select[id$="-estado"], select[name="estado"]`);
        
        if (!estadoField) {
            console.log('No se encontró el campo estado');
            return;
        }
        
        // Obtener información del material
        const materialId = obtenerMaterialId();
        if (!materialId) {
            console.log('No se pudo obtener el ID del material');
            return;
        }
        
        // Obtener información del material via AJAX
        obtenerInfoMaterial(materialId, function(materialInfo) {
            if (materialInfo) {
                const nuevoEstado = calcularEstado(cantidad, materialInfo.stock_minimo, materialInfo.descontinuado);
                aplicarEstado(estadoField, nuevoEstado);
            }
        });
    }
    
    // Obtener el ID del material del formulario
    function obtenerMaterialId() {
        // Buscar select de material
        const materialSelect = document.querySelector('select[id$="-id_material"], select[name="id_material"]');
        if (materialSelect && materialSelect.value) {
            return materialSelect.value;
        }
        
        return null;
    }
    
    // Obtener información del material via AJAX
    function obtenerInfoMaterial(materialId, callback) {
        const url = `/admin/Compras/inventariomateriale/obtener_info_material/${materialId}/`;
        
        fetch(url)
        .then(response => response.json())
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
    
    // Aplicar el estado al campo select - USANDO TUS IDs
    function aplicarEstado(estadoField, nuevoEstado) {
        const estadoId = ESTADOS_IDS[nuevoEstado];
        
        if (!estadoId) {
            console.error(`ID no encontrado para estado: ${nuevoEstado}`);
            return;
        }

        // Establecer el valor (ID del estado)
        estadoField.value = estadoId;

        // Disparar eventos de cambio
        estadoField.dispatchEvent(new Event('change', { bubbles: true }));

        console.log(`Estado actualizado: ${nuevoEstado} (ID: ${estadoId})`);
    }
    
    // Obtener el prefijo del campo para formularios inline
    function getFieldPrefix(input) {
        const id = input.id;
        if (id.includes('-cantidad_disponible')) {
            return id.split('-cantidad_disponible')[0] + '-';
        }
        return '';
    }
    
    // Inicializar
    if (window.location.pathname.includes('/inventariomateriale/')) {
        setTimeout(() => {
            setupCantidadDisponibleListeners();
            
            // También escuchar cambios en el material
            const materialSelect = document.querySelector('select[id$="-id_material"]');
            if (materialSelect) {
                materialSelect.addEventListener('change', function() {
                    setTimeout(() => setupCantidadDisponibleListeners(), 100);
                });
            }
        }, 500);
    }
});