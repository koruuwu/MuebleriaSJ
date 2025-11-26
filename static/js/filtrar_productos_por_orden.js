document.addEventListener("DOMContentLoaded", function() {
    // Función para filtrar productos basado en la lista de compra
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            document.querySelectorAll('input[id$="-cantidad_recibida"]').forEach(input => {
                if (input.dataset.visualValue) {
                    input.value = input.dataset.visualValue;
                }
            });
        });
    }


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
            // No borramos el valor guardado, lo mantenemos
            const currentValue = select.value;
            select.innerHTML = currentValue ? `<option value="${currentValue}">Cargando producto guardado...</option>` : '<option value="">Cargando productos...</option>';
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
                // Solo reiniciamos opciones si la opción actual no existe en la lista nueva
                select.innerHTML = '<option value="">---------</option>';
                
                data.forEach(producto => {
                    const option = document.createElement('option');
                    option.value = producto.id;
                    option.textContent = `${producto.nombre} (Req: ${producto.cantidad_necesaria})`;
                    option.setAttribute('data-cantidad', producto.cantidad_necesaria);
                    
                    // Mantener seleccionado el valor guardado
                    if (currentValue == producto.id) {
                        option.selected = true;
                        autocompletarCantidadOrd(select, producto.cantidad_necesaria);
                    }
                    
                    select.appendChild(option);
                });

                // Si el valor guardado no estaba en la lista, crear opción temporal
                if (currentValue && !Array.from(select.options).some(o => o.value == currentValue)) {
                    const opt = document.createElement('option');
                    opt.value = currentValue;
                    opt.textContent = 'Valor guardado';
                    opt.selected = true;
                    select.appendChild(opt);
                }
                
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
    
    
    // Función para autocompletar cantidad_ord (MODIFICADA para usar APORTE)
    function autocompletarCantidadOrd(productSelect, cantidadNecesaria) {
        console.log('Autocompletando cantidad:', cantidadNecesaria);

        const prefix = productSelect.id.split('-product')[0];
        const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
        const aporteInput = document.querySelector(`#${prefix}-aporte`);
        const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);

        if (cantidadOrdInput) {
            cantidadOrdInput.value = cantidadNecesaria;
            console.log('✓ Valor asignado a cantidad_ord:', cantidadOrdInput.value);

            cantidadOrdInput.dispatchEvent(new Event('change', { bubbles: true }));
            cantidadOrdInput.dispatchEvent(new Event('input', { bubbles: true }));
        }

        // Inicializar aporte como la cantidad necesaria (puede ser modificado después)
        if (aporteInput && !aporteInput.value) {
            aporteInput.value = cantidadNecesaria;
            console.log('Valor inicial de aporte:', aporteInput.value);
            
            // Disparar eventos para actualizar estado
            aporteInput.dispatchEvent(new Event('change', { bubbles: true }));
            aporteInput.dispatchEvent(new Event('input', { bubbles: true }));
        }

        // Actualizar estado basado en el APORTE actual
        if (aporteInput && estadoItemSelect && cantidadNecesaria > 0) {
            actualizarEstadoItem(aporteInput, cantidadNecesaria, estadoItemSelect);
        }
    }

    // Función para actualizar estado_item basado en cantidad_recibida vs cantidad_ord
    function setupCantidadRecibidaListeners() {
        // Escuchar cambios en todos los inputs de cantidad_recibida
        document.addEventListener('input', function(event) {
            if (event.target.matches('input[id$="-cantidad_recibida"]')) {
                actualizarEstadoDesdeCantidadRecibida(event.target);
            }
        });

        // También escuchar eventos change
        document.addEventListener('change', function(event) {
            if (event.target.matches('input[id$="-cantidad_recibida"]')) {
                actualizarEstadoDesdeCantidadRecibida(event.target);
            }
        });
    }

    // Nueva función para actualizar estado desde cantidad_recibida
    function actualizarEstadoDesdeCantidadRecibida(input) {
        const prefix = input.id.split('-cantidad_recibida')[0];
        
        const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
        const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);
        const cantidadRecibida = parseInt(input.value || 0, 10);
        
        if (cantidadOrdInput && estadoItemSelect) {
            const cantidadOrd = parseInt(cantidadOrdInput.value || 0, 10);
            
            console.log(`Cantidad recibida: ${cantidadRecibida}, Cantidad ord: ${cantidadOrd}`);
            
            if (cantidadRecibida === cantidadOrd) {
                estadoItemSelect.value = 'completo';
                console.log('✓ Estado cambiado a COMPLETO por cantidad_recibida');
            } else if (cantidadRecibida > cantidadOrd) {
                estadoItemSelect.value = 'excedido';
                console.log('✓ Estado cambiado a EXCEDIDO por cantidad_recibida');
            } else if (cantidadRecibida > 0) {
                estadoItemSelect.value = 'incompleto';
                console.log('✓ Estado cambiado a INCOMPLETO por cantidad_recibida');
            }
            
            // ACTUALIZAR ESTADO DE LA LISTA
            actualizarEstadoLista();
            
            // Actualizar Select2 si aplica
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery(estadoItemSelect).trigger('change.select2');
            }
        }
    }

    // Función para actualizar el estado del ítem (MODIFICADA - versión simplificada)
    function actualizarEstadoItem(aporteInput, cantidadNecesaria, estadoItemSelect) {
        const aporte = parseInt(aporteInput.value || 0, 10);
        const prefix = aporteInput.id.split('-aporte')[0];

        const cantidadRecibidaInput = document.querySelector(`#${prefix}-cantidad_recibida`);
        let cantidadRecibidaBase = cantidadRecibidaInput ? parseInt(cantidadRecibidaInput.dataset.baseValue || 0, 10) : 0;

        // Nueva cantidad recibida = base + aporte
        const nuevaCantidadRecibida = cantidadRecibidaBase + aporte;

        if (cantidadRecibidaInput) {
            // Solo mostrar visualmente, NO modificar value
            cantidadRecibidaInput.dataset.visualValue = nuevaCantidadRecibida;

            // Mostrar visualmente en el input con un texto temporal
            cantidadRecibidaInput.placeholder = nuevaCantidadRecibida; // ❌ solo visual

            // Guardar baseValue si aún no existe
            if (!cantidadRecibidaInput.dataset.baseValue) {
                cantidadRecibidaInput.dataset.baseValue = cantidadRecibidaInput.value || 0;
            }

            console.log(`Cantidad recibida visual: ${nuevaCantidadRecibida}`);
        }

        // Determinar estado del item
        if (nuevaCantidadRecibida === cantidadNecesaria) {
            estadoItemSelect.value = 'completo';
        } else if (nuevaCantidadRecibida > cantidadNecesaria) {
            estadoItemSelect.value = 'excedido';
        } else {
            estadoItemSelect.value = 'incompleto';
        }

        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(estadoItemSelect).trigger('change.select2');
        }

        actualizarEstadoLista();
        console.log(`✓ Estado actualizado a: ${estadoItemSelect.value}`);
    }



    // Función para configurar listeners de APORTE
    function setupAporteListeners() {
        // Escuchar cambios en todos los inputs de APORTE
        document.addEventListener('input', function(event) {
            if (event.target.matches('input[id$="-aporte"]')) {
                const input = event.target;
                const prefix = input.id.split('-aporte')[0];
                
                const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
                const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);
                const productSelect = document.querySelector(`#${prefix}-product`);
                
                if (cantidadOrdInput && estadoItemSelect && productSelect) {
                    const cantidadNecesaria = parseInt(cantidadOrdInput.value || 0, 10);
                    
                    if (cantidadNecesaria > 0) {
                        actualizarEstadoItem(input, cantidadNecesaria, estadoItemSelect);
                    } else {
                        // Si no hay cantidad ordenada, intentar obtener del producto seleccionado
                        const selectedOption = productSelect.options[productSelect.selectedIndex];
                        if (selectedOption && selectedOption.value) {
                            const cantidadNecesariaFromProduct = selectedOption.getAttribute('data-cantidad');
                            if (cantidadNecesariaFromProduct) {
                                actualizarEstadoItem(input, parseInt(cantidadNecesariaFromProduct, 10), estadoItemSelect);
                            }
                        }
                    }
                }
            }
        });

        // También escuchar eventos change para mayor compatibilidad
        document.addEventListener('change', function(event) {
            if (event.target.matches('input[id$="-aporte"]')) {
                const input = event.target;
                const prefix = input.id.split('-aporte')[0];
                
                const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
                const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);
                
                if (cantidadOrdInput && estadoItemSelect) {
                    const cantidadNecesaria = parseInt(cantidadOrdInput.value || 0, 10);
                    if (cantidadNecesaria > 0) {
                        actualizarEstadoItem(input, cantidadNecesaria, estadoItemSelect);
                    }
                }
            }
        });
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

    // FUNCIÓN MEJORADA: Actualizar estado de lista cuando todos los items estén completos
    function actualizarEstadoLista() {
        const estadoListaSelect = document.querySelector('#id_estado'); 
        if (!estadoListaSelect) return;

        const estadosItem = document.querySelectorAll('select[id$="-estado_item"]');
        if (estadosItem.length === 0) return;

        // Verificar si TODOS los items están en 'completo' y no están vacíos
        const itemsConValor = Array.from(estadosItem).filter(select => select.value !== '');
        const todosCompletos = itemsConValor.length > 0 && 
                              itemsConValor.every(select => select.value === 'completo');

        console.log(`Items totales: ${estadosItem.length}, Items con valor: ${itemsConValor.length}, Todos completos: ${todosCompletos}`);

        if (todosCompletos) {
            estadoListaSelect.value = 'completa'; // CORREGIDO: 'completa' no 'completo'
            console.log("✓ La lista completa pasó a COMPLETA porque todos los items están completos");

            // Actualizar select2 si aplica
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery(estadoListaSelect).trigger('change.select2');
            }
        } else {
            console.log("✗ La lista NO está completa - algunos items no están completos");
        }
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
            
            // ACTUALIZAR ESTADO DE LA LISTA AL INICIO
            actualizarEstadoLista();
        }, 1000);
    }
    
    // Inicializar
    if (window.location.pathname.includes('/listacompra/')) {
        setTimeout(() => {
            filtrarProductosPorListaCompra();
            setupSelect2Listener();
            setupAporteListeners();
            setupCantidadRecibidaListeners();
            actualizarEstadosExistentes();
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
                                setupAporteListeners();
                                setupCantidadRecibidaListeners();
                                actualizarEstadosExistentes();
                                
                                // ACTUALIZAR ESTADO DE LA LISTA CUANDO SE AÑADEN NUEVAS FILAS
                                actualizarEstadoLista();
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