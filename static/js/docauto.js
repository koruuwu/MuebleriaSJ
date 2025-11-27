document.addEventListener("DOMContentLoaded", function() {
    // ========== CONFIGURACIÓN INICIAL ==========
    const isListaCompraPage = window.location.pathname.includes('/listacompra/');
    if (!isListaCompraPage) return;

    // ========== FUNCIONES AUXILIARES ==========
    function getPrefixFromId(id, suffix) {
        return id.replace(suffix, "");
    }

    function getCurrentListaCompraId() {
        const urlMatch = window.location.pathname.match(/listacompra\/(\d+)\/change/);
        if (urlMatch) return urlMatch[1];
        
        const idField = document.querySelector('input[name="id"]');
        return idField?.value || null;
    }

    // ========== SISTEMA DE COMENTARIOS PARA CANTIDAD ==========
    function inicializarSistemaCantidad() {
        document.querySelectorAll('input[id$="-cantidad_recibida"]').forEach(input => {
            if (!input.dataset.baseValue) {
                input.dataset.baseValue = input.value || 0;
            }
            const prefix = getPrefixFromId(input.id, '-cantidad_recibida');
            crearComentarioCantidad(prefix);
            actualizarComentarioCantidad(prefix);
            actualizarVisualCantidadRecibida(prefix);
        });
    }

    function crearComentarioCantidad(prefix) {
        const input = document.querySelector(`#${prefix}-cantidad_recibida`);
        if (!input || input.dataset.hasComment) return;

        const small = document.createElement('small');
        Object.assign(small.style, {
            display: "block",
            fontSize: "11px",
            color: "#555"
        });
        small.id = `${prefix}-comentario-cant`;
        input.insertAdjacentElement("afterend", small);
        input.dataset.hasComment = "true";
    }

    function actualizarComentarioCantidad(prefix) {
        const input = document.querySelector(`#${prefix}-cantidad_recibida`);
        const small = document.querySelector(`#${prefix}-comentario-cant`);
        if (!input || !small) return;

        const base = parseInt(input.dataset.baseValue || 0, 10);
        const visual = parseInt(input.dataset.visualValue || base, 10);
        small.textContent = `Cantidad final recibida: ${visual}`;
    }

    function actualizarVisualCantidadRecibida(prefix) {
        const cantidadRecibidaInput = document.querySelector(`#${prefix}-cantidad_recibida`);
        const aporteInput = document.querySelector(`#${prefix}-aporte`);
        if (!cantidadRecibidaInput) return;

        const base = parseInt(cantidadRecibidaInput.dataset.baseValue || 0, 10);
        const aporte = parseInt(aporteInput?.value || 0, 10);
        const visual = base + aporte;

        cantidadRecibidaInput.dataset.visualValue = visual;
        cantidadRecibidaInput.placeholder = visual;
        actualizarComentarioCantidad(prefix);
    }

    // ========== FILTRADO DE PRODUCTOS ==========
    function filtrarProductosPorListaCompra() {
        const listaCompraId = getCurrentListaCompraId();
        const productSelects = document.querySelectorAll('select[id$="-product"]');
        
        if (!listaCompraId) {
            productSelects.forEach(select => {
                select.innerHTML = '<option value="">Seleccione una lista de compra primero</option>';
                select.disabled = true;
            });
            return;
        }
        
        productSelects.forEach(select => {
            select.disabled = false;
            const currentValue = select.value;
            select.innerHTML = currentValue ? 
                `<option value="${currentValue}">Cargando producto guardado...</option>` : 
                '<option value="">Cargando productos...</option>';
        });
        
        fetch(`/admin/Compras/listacompra/obtener_productos_por_lista/${listaCompraId}/`, {
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
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

                if (currentValue && !Array.from(select.options).some(o => o.value == currentValue)) {
                    const opt = document.createElement('option');
                    opt.value = currentValue;
                    opt.textContent = 'Valor guardado';
                    opt.selected = true;
                    select.appendChild(opt);
                }
                
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

    // ========== AUTOMATIZACIÓN DE CANTIDADES ==========
    function autocompletarCantidadOrd(productSelect, cantidadNecesaria) {
        const prefix = productSelect.id.split('-product')[0];
        const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
        const aporteInput = document.querySelector(`#${prefix}-aporte`);
        const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);

        if (cantidadOrdInput) {
            cantidadOrdInput.value = cantidadNecesaria;
            cantidadOrdInput.dispatchEvent(new Event('change', { bubbles: true }));
        }

        if (aporteInput && !aporteInput.value) {
            aporteInput.value = cantidadNecesaria;
            aporteInput.dispatchEvent(new Event('change', { bubbles: true }));
        }

        if (aporteInput && estadoItemSelect && cantidadNecesaria > 0) {
            actualizarEstadoItem(prefix, cantidadNecesaria);
        }
    }

    // ========== GESTIÓN DE ESTADOS ==========
    function actualizarEstadoItem(prefix, cantidadNecesaria) {
        const aporteInput = document.querySelector(`#${prefix}-aporte`);
        const cantidadRecibidaInput = document.querySelector(`#${prefix}-cantidad_recibida`);
        const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);

        if (!cantidadRecibidaInput || !estadoItemSelect) return;

        if (!cantidadRecibidaInput.dataset.baseValue) {
            cantidadRecibidaInput.dataset.baseValue = cantidadRecibidaInput.value || 0;
        }

        const base = parseInt(cantidadRecibidaInput.dataset.baseValue, 10);
        const aporte = parseInt(aporteInput?.value || 0, 10);
        const nuevaCantidad = base + aporte;

        if (nuevaCantidad === cantidadNecesaria) {
            estadoItemSelect.value = 'completo';
        } else if (nuevaCantidad > cantidadNecesaria) {
            estadoItemSelect.value = 'excedido';
        } else {
            estadoItemSelect.value = 'incompleto';
        }

        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(estadoItemSelect).trigger('change.select2');
        }

        actualizarEstadoLista();
        actualizarComentarioCantidad(prefix);
    }

    function actualizarEstadoLista() {
        const estadoListaSelect = document.querySelector('#id_estado');
        const estadosItem = document.querySelectorAll('select[id$="-estado_item"]');
        
        if (!estadoListaSelect || estadosItem.length === 0) return;

        const itemsConValor = Array.from(estadosItem).filter(select => select.value !== '');
        const todosCompletos = itemsConValor.length > 0 && 
                              itemsConValor.every(select => select.value === 'completo');

        if (todosCompletos) {
            estadoListaSelect.value = 'completa';
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery(estadoListaSelect).trigger('change.select2');
            }
        }
    }

    // ========== EVENT LISTENERS SIMPLIFICADOS ==========
    function setupEventListeners() {
        // Listener único para el formulario
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

        // Listeners unificados para inputs
        document.addEventListener('input', function(event) {
            const target = event.target;
            
            if (target.matches('input[id$="-aporte"]')) {
                const prefix = target.id.split('-aporte')[0];
                const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
                
                if (cantidadOrdInput) {
                    const cantidadNecesaria = parseInt(cantidadOrdInput.value || 0, 10);
                    if (cantidadNecesaria > 0) {
                        actualizarEstadoItem(prefix, cantidadNecesaria);
                    }
                }
                actualizarVisualCantidadRecibida(prefix);
            }
            
            if (target.matches('input[id$="-cantidad_recibida"]')) {
                const prefix = target.id.split('-cantidad_recibida')[0];
                actualizarEstadoDesdeCantidadRecibida(target);
            }
        });

        // Listener para cambios en selects de productos
        document.addEventListener('change', function(event) {
            if (event.target.matches('select[id$="-product"]')) {
                const selectedOption = event.target.options[event.target.selectedIndex];
                const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                
                if (cantidadNecesaria) {
                    autocompletarCantidadOrd(event.target, cantidadNecesaria);
                }
            }
        });

        // Listener para Select2 si está disponible
        if (window.jQuery && window.jQuery.fn.select2) {
            $(document).on('select2:select', 'select[id$="-product"]', function(e) {
                const selectedOption = e.target.options[e.target.selectedIndex];
                const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                
                if (cantidadNecesaria) {
                    setTimeout(() => autocompletarCantidadOrd(e.target, cantidadNecesaria), 100);
                }
            });
        }
    }

    function actualizarEstadoDesdeCantidadRecibida(input) {
        const prefix = input.id.split('-cantidad_recibida')[0];
        const cantidadOrdInput = document.querySelector(`#${prefix}-cantidad_ord`);
        const estadoItemSelect = document.querySelector(`#${prefix}-estado_item`);
        const cantidadRecibida = parseInt(input.value || 0, 10);
        
        if (cantidadOrdInput && estadoItemSelect) {
            const cantidadOrd = parseInt(cantidadOrdInput.value || 0, 10);
            
            if (cantidadRecibida === cantidadOrd) {
                estadoItemSelect.value = 'completo';
            } else if (cantidadRecibida > cantidadOrd) {
                estadoItemSelect.value = 'excedido';
            } else if (cantidadRecibida > 0) {
                estadoItemSelect.value = 'incompleto';
            }
            
            actualizarEstadoLista();
            
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery(estadoItemSelect).trigger('change.select2');
            }
        }
        actualizarComentarioCantidad(prefix);
    }

    // ========== INICIALIZACIÓN ==========
    function inicializar() {
        filtrarProductosPorListaCompra();
        setupEventListeners();
        inicializarSistemaCantidad();
        actualizarEstadoLista();

        // Forzar actualización inicial después de un breve delay
        setTimeout(() => {
            document.querySelectorAll('select[id$="-product"]').forEach(select => {
                if (select.value) {
                    const selectedOption = select.options[select.selectedIndex];
                    const cantidadNecesaria = selectedOption.getAttribute('data-cantidad');
                    if (cantidadNecesaria) {
                        autocompletarCantidadOrd(select, cantidadNecesaria);
                    }
                }
            });
        }, 500);
    }

    // Observar nuevas filas dinámicas
    const observer = new MutationObserver(function(mutations) {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === 1 && node.querySelector('select[id$="-product"]')) {
                    setTimeout(() => {
                        filtrarProductosPorListaCompra();
                        inicializarSistemaCantidad();
                        actualizarEstadoLista();
                    }, 200);
                    break;
                }
            }
        }
    });
