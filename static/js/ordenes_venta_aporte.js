console.log("JS de aporte cargado (inicio)");

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOMContentLoaded disparado");

    const path = window.location.pathname;
    console.log("Ruta actual:", path);

    const isOrdenesVentaPage = path.includes('/ordenesventa/');
    console.log("¿Es página de órdenes?", isOrdenesVentaPage);

    if (!isOrdenesVentaPage) {
        console.warn("No es página de ordenesventa script detenido");
        return;
    }
    const metodoPagoSelect = document.querySelector('#id_id_metodo_pago');
    const tarjetaInput = document.querySelector('#id_num_tarjeta');
    const aporteInput = document.querySelector('#id_aporte');
    const pagadoInput = document.querySelector('#id_pagado');
    const totalInput = document.querySelector('#id_total');
    const estadoPagoSelect = document.querySelector('#id_id_estado_pago');
    const cuotasInput = document.querySelector('#id_cuotas');  // <-- AQUI
    const efectivoInput = document.querySelector('#id_efectivo');  // <-- AQUI

    pagadoInput.readOnly= true;
    

    console.log("aporteInput:", aporteInput);
    console.log("pagadoInput:", pagadoInput);
    console.log("totalInput:", totalInput);
    console.log("estadoPagoSelect:", estadoPagoSelect);
    console.log("cuotasInput:", cuotasInput);

    if (!aporteInput || !pagadoInput || !totalInput || !estadoPagoSelect || !cuotasInput) {
        console.error("Faltan uno o más inputs necesarios. Abortando script.");
        return;
    }

    console.log("Todos los inputs encontrados correctamente.");

    // ---- DEPURAR SI EL CAMBIO DE CUOTAS FUNCIONA ----
    cuotasInput.addEventListener("change", function () {
        console.log("Evento change en cuotas → NUEVO VALOR:", cuotasInput.checked);
    });

    function limpiarNumero(valor) {
        if (!valor) return 0;
        return parseFloat(valor.replace(/,/g, '')) || 0;
    }

   

    function actualizarEstiloDeshabilitado() {
        const campos = [aporteInput, pagadoInput, totalInput, estadoPagoSelect, cuotasInput, tarjetaInput, efectivoInput];
        //agregar todos los input que tienen permitido ponerse en gris
        campos.forEach(campo => {
            if (campo.readOnly) {
                campo.style.backgroundColor = "#f0f0f0ff";  // gris claro
                campo.style.color = "#999999ff";  // texto gris oscuro
            } else {
                campo.style.backgroundColor = "";  // reset
                campo.style.color = "";  // reset
            }
        });
    }

    
    // Crear mensaje pagado
    let mensaje = document.querySelector('#mensaje-pagado');
    if (!mensaje) {
        console.log("Creando mensaje debajo del pagado");
        mensaje = document.createElement('small');
        mensaje.id = "mensaje-pagado";
        mensaje.style.display = 'block';
        mensaje.style.fontSize = '12px';
        mensaje.style.fontWeight = 'bold';
        mensaje.style.marginTop = '4px';
        pagadoInput.insertAdjacentElement("afterend", mensaje);
    }

    function actualizarCamposPorMetodoPago() {
        const valor = parseInt(metodoPagoSelect.value);
        console.log("Metodo de pago seleccionado " + valor);
        cuotasInput.disabled = false; // desbloquear por defecto
        cuotasInput.checked = false;


        switch (valor) {
            case 1: // Efectivo
                tarjetaInput.readOnly = true;
                cuotasInput.readOnly = false;
                efectivoInput.readOnly=true;
                
                break;
            case 2: // Tarjeta
                cuotasInput.readOnly = false;
                tarjetaInput.readOnly = false;
                break;
            case 3: // Transferencia
                cuotasInput.checked = false;
                cuotasInput.readOnly = false;
                tarjetaInput.readOnly = true;
                efectivoInput.readOnly=true;
                break;
            case 4: // Mixto
                cuotasInput.checked = false;
                cuotasInput.disabled = true;
                tarjetaInput.readOnly = false;
                efectivoInput.readOnly=false;
                
                break;
            default:
                cuotasInput.readOnly = true;
                tarjetaInput.readOnly = true;
                efectivoInput.readOnly=true;

                

        }

        actualizarEstiloDeshabilitado();

        // Si quieres que Select2 refleje el cambio en el select, usa esto:
        if ($(metodoPagoSelect).hasClass('select2-hidden-accessible')) {
            $(metodoPagoSelect).trigger('change.select2');
        }
    }

    actualizarCamposPorMetodoPago();

    // ---- FUNCIÓN PARA HABILITAR/DESHABILITAR APORTES ----
    function actualizarHabilitadoAporte() {
        console.log("Ejecutando actualizarHabilitadoAporte()");
        console.log("Valor actual de cuotasInput.checked =", cuotasInput.checked);
        let totall=totalInput.value;

        if (cuotasInput.checked) {
            console.log("Cuotas activado  habilitando aporte");
            aporteInput.readOnly = false;
            pagadoInput.readOnly= true;
        } else {
            console.log("Cuotas desactivado  deshabilitando aporte");
            pagadoInput.value= totall;
            aporteInput.readOnly = true;
            aporteInput.value = 0;
            actualizarPagado();
            console.log("total: "+totall)
        }
        actualizarEstiloDeshabilitado();
    }

    // Ejecutar inicial
    console.log("Llamando actualizarHabilitadoAporte() al cargar");
    actualizarHabilitadoAporte();

    // Vincular a cambios
    cuotasInput.addEventListener('change', actualizarHabilitadoAporte);

    // Guardar base original
    if (!pagadoInput.dataset.baseValue) {
        pagadoInput.dataset.baseValue = limpiarNumero(pagadoInput.value || 0);
        console.log("Base inicial pagado:", pagadoInput.dataset.baseValue);
    }




    function actualizarEstadoPago(total, pagado) {
        console.log("actualizarEstadoPago() total:", total, " pagado:", pagado);

        let estadoPagadoId = null;
        let estadoPendienteId = null;

        [...estadoPagoSelect.options].forEach(opt => {
            const texto = opt.textContent.trim().toLowerCase();
            if (texto === "pagado") estadoPagadoId = opt.value;
            if (texto === "pendiente") estadoPendienteId = opt.value;
        });

        let nuevoValor = estadoPendienteId; // por defecto pendiente
        let mensajeColor = "red";
        let mensajeTexto = `Pagado: L. ${pagado.toFixed(2)} (PENDIENTE)`;

        if (!isNaN(total) && !isNaN(pagado) && pagado == total && estadoPagadoId) {
            nuevoValor = estadoPagadoId;
            mensajeColor = "green";
            mensajeTexto = `Pagado: L. ${pagado.toFixed(2)} (COMPLETO)`;
        }

        if (!isNaN(total) && !isNaN(pagado) && pagado > total && estadoPagadoId) {
            nuevoValor = estadoPagadoId;
            mensajeColor = "red";
            mensajeTexto = `Pagado: L. ${pagado.toFixed(2)} (EXEDIDO)`;
        }

        // Actualizar select
        if ($(estadoPagoSelect).hasClass('select2-hidden-accessible')) {
            $(estadoPagoSelect).val(nuevoValor).trigger('change');
        } else {
            estadoPagoSelect.value = nuevoValor;
        }

        // Actualizar mensaje
        mensaje.style.color = mensajeColor;
        mensaje.textContent = mensajeTexto;
    }

    let mensaje_ta = document.querySelector('#mensaje-ta');
    if (!mensaje_ta) {
        console.log("Creando mensaje debajo de efectivo");
        mensaje_ta = document.createElement('small');
        mensaje_ta.id = "mensaje-ta";
        mensaje_ta.style.display = 'block';
        mensaje_ta.style.fontSize = '12px';
        mensaje_ta.style.fontWeight = 'bold';
        mensaje_ta.style.marginTop = '4px';
        efectivoInput.insertAdjacentElement("afterend", mensaje_ta);
    }

    

    function actualizarPagado() {
        const base = limpiarNumero(pagadoInput.dataset.baseValue || 0);
        const aporte = limpiarNumero(aporteInput.value || 0);
        const total = limpiarNumero(totalInput.value || 0);

        // Si aporte está deshabilitado, simplemente pagado = total
        if (aporteInput.readOnly) {
            pagadoInput.value = total.toFixed(2);
        } else {
            const nuevoPagado = base + aporte;
            pagadoInput.value = nuevoPagado.toFixed(2);
        }

        actualizarEstadoPago(total, limpiarNumero(pagadoInput.value));

        efectivoInput.addEventListener('input', function () {
            const total = limpiarNumero(totalInput.value || 0);
            const efectivo = limpiarNumero(efectivoInput.value || 0);

            // Calcular lo que falta pagar con tarjeta
            const tarjetaFaltante = Math.max(total - efectivo, 0);

            // Mostrar mensaje en el mismo elemento 'mensaje'
             // color opcional

            if(total==efectivo){
                mensaje_ta.style.color = "red"; // color opcional
                mensaje_ta.textContent = `Para deposito completo se recomienda el metodo de pago efectivo`;  
            }else {
                if (total<efectivo) {
                mensaje_ta.style.color = "red"; // color opcional
                mensaje_ta.textContent = `Deposito EXEDIDO no puede superar al total`;  
                    
                } else {
                    mensaje_ta.style.color = "green";
                    mensaje_ta.textContent = `Depósito en tarjeta: L. ${tarjetaFaltante.toFixed(2)}`; 
                }
                
            }

            // También actualizar pagado total si quieres reflejarlo
            efectivo.insertAdjacentElement("afterend", mensaje_ta);

        });
    }
    
    
    // Observar cambios en totalInput
    totalInput.addEventListener('totalActualizado', function() {
        console.log("Evento totalActualizado capturado");
        console.log("totalInput.value:", totalInput.value);
        console.log("aporteInput.readOnly:", aporteInput.readOnly);
        if (aporteInput.readOnly) {
            console.log("Total actualizado por otro JS → actualizando pagado");
            actualizarPagado();
        }
    });

    $(metodoPagoSelect).on('change', function () {
        actualizarCamposPorMetodoPago();
        actualizarHabilitadoAporte(); // actualiza aporte/pagado según cuotas
    });





    aporteInput.addEventListener('input', function () {
        console.log("Evento input en aporte:", aporteInput.value);
        actualizarPagado();
    });

    console.log("Ejecutando actualizarPagado() inicial");
    actualizarPagado();

    

    
});
