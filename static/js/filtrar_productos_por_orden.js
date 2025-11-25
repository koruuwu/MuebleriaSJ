document.addEventListener("DOMContentLoaded", function() {
    // Función para filtrar productos basado en la lista de compra
    function filtrarProductosPorListaCompra() {
        const listaCompraId = getCurrentListaCompraId();
        const productSelects = document.querySelectorAll('select[id$="-product"]');
        
        if (!listaCompraId || listaCompraId === '') {
            productSelects.forEach(select => {
                select.innerHTML = '<option value="">Seleccione una lista de compra primero</option>';
                select.disabled = true;
            });
            return;
        }
        
        productSelects.forEach(select => {
            select.disabled = false;
            select.innerHTML = '<option value="">Cargando productos...</option>';
        });
        
        const url = `/admin/Compras/listacompra/obtener_productos_por_lista/${listaCompraId}/`;
        
        fetch(url, {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Datos recibidos:', data);
            productSelects.forEach(select => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">---------</option>';
                
                data.forEach(producto => {
                    const option = document.createElement('option');
                    option.value = producto.id;
                    option.textContent = `${producto.nombre} (Req: ${producto.cantidad_necesaria})`;
                    option.setAttribute('data-cantidad', producto.cantidad_necesaria);
                    
                    if (currentValue == producto.id) {
                        option.selected = true;
                        autocompletarCantidadOrd(select, producto.cantidad_necesaria);
                    }
                    
                    select.appendChild(option);
                });
                
                // Actualizar Select2
                if (window.jQuery && window.jQuery.fn.select2) {
                    window.jQuery(select).trigger('change.select2');
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
            productSelects.forEach(select => {
                select.innerHTML = '<option value="">Error al cargar</option>';
            });
        });
    }
    
    // Función para autocompletar cantidad_ord
    function autocompletarCantidadOrd(productSelect, cantidadNecesaria) {
        console.log('Autocompletando cantidad:', cantidadNecesaria);
        
        const prefix = productSelect.id.split('-product')[0];
        const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
        
        if (cantidadOrdInput) {
            cantidadOrdInput.value = cantidadNecesaria;
            console.log('✓ Valor asignado a cantidad_ord:', cantidadOrdInput.value);
            
            cantidadOrdInput.dispatchEvent(new Event('change', { bubbles: true }));
            cantidadOrdInput.dispatchEvent(new Event('input', { bubbles: true }));
            
            // Actualizar estado del item
            const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);
            if (estadoItemSelect && cantidadNecesaria > 0) {
                estadoItemSelect.value = 'completo';
                if (window.jQuery && window.jQuery.fn.select2) {
                    window.jQuery(estadoItemSelect).trigger('change.select2');
                }
            }
        }
    }
    
    // Función MEJORADA para manejar Select2
    function setupSelect2Listener() {
        // Método 1: Usar eventos de Select2 si jQuery está disponible
        if (window.jQuery && window.jQuery.fn.select2) {
            $(document).on('select2:select', 'select[id$="-product"]', function(e) {
                console.log('Select2 event triggered');
                const select = e.target;
                const selectedOption = select.options[select.selectedIndex];
                const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                
                console.log('Select2 - Cantidad necesaria:', cantidadNecesaria);
                
                if (cantidadNecesaria) {
                    setTimeout(() => {
                        autocompletarCantidadOrd(select, cantidadNecesaria);
                    }, 100);
                }
            });
        }
        
        // Método 2: Observar cambios en el DOM para detectar selecciones de Select2
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        // Detectar cuando Select2 abre el dropdown
                        if (node.nodeType === 1 && 
                            node.classList && 
                            (node.classList.contains('select2-results__options') || 
                             node.classList.contains('select2-dropdown'))) {
                            
                            // Cuando se hace click en una opción del dropdown
                            node.addEventListener('click', function(e) {
                                setTimeout(() => {
                                    const selects = document.querySelectorAll('select[id$="-product"]');
                                    selects.forEach(select => {
                                        if (select.value) {
                                            const selectedOption = select.options[select.selectedIndex];
                                            const cantidad = selectedOption.getAttribute('data-cantidad');
                                            if (cantidad) {
                                                autocompletarCantidadOrd(select, cantidad);
                                            }
                                        }
                                    });
                                }, 200);
                            });
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Método 3: Escuchar cambios en los selects ocultos (fallback)
        document.addEventListener('change', function(event) {
            if (event.target.matches('select[id$="-product"]') && !event.target.classList.contains('select2-hidden-accessible')) {
                const selectedOption = event.target.options[event.target.selectedIndex];
                const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                
                if (cantidadNecesaria) {
                    autocompletarCantidadOrd(event.target, cantidadNecesaria);
                }
            }
        });
        
        // Método 4: Escuchar clicks en cualquier parte y verificar si hay cambios
        document.addEventListener('click', function() {
            setTimeout(() => {
                const selects = document.querySelectorAll('select[id$="-product"]');
                selects.forEach(select => {
                    if (select.value) {
                        const selectedOption = select.options[select.selectedIndex];
                        const cantidad = selectedOption.getAttribute('data-cantidad');
                        if (cantidad) {
                            // Verificar si el valor ya está asignado
                            const prefix = select.id.split('-product')[0];
                            const cantidadInput = document.querySelector(`#${prefix}-cantidad_ord`);
                            if (cantidadInput && cantidadInput.value !== cantidad) {
                                autocompletarCantidadOrd(select, cantidad);
                            }
                        }
                    }
                });
            }, 300);
        });
    }
    
    // Obtener ID de lista de compra
    function getCurrentListaCompraId() {
        const urlMatch = window.location.pathname.match(/listacompra\/(\d+)\/change/);
        if (urlMatch) return urlMatch[1];
        
        const idField = document.querySelector('input[name="id"]');
        if (idField && idField.value) return idField.value;
        
        return null;
    }
    
    // Función para forzar la actualización
    function forzarActualizacionInicial() {
        setTimeout(() => {
            const productSelects = document.querySelectorAll('select[id$="-product"]');
            productSelects.forEach(select => {
                if (select.value) {
                    const selectedOption = select.options[select.selectedIndex];
                    const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                    if (cantidadNecesaria) {
                        autocompletarCantidadOrd(select, cantidadNecesaria);
                    }
                }
            });
        }, 1000);
    }
    
    // Inicializar
    if (window.location.pathname.includes('/listacompra/')) {
        setTimeout(() => {
            filtrarProductosPorListaCompra();
            setupSelect2Listener();
            forzarActualizacionInicial();
        }, 100);
        
        // Observar nuevas filas
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.querySelector('select[id$="-product"]')) {
                            setTimeout(() => {
                                filtrarProductosPorListaCompra();
                                setupSelect2Listener();
                            }, 200);
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
});