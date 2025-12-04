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

    const aporteInput = document.querySelector('#id_aporte');
    const pagadoInput = document.querySelector('#id_pagado');
    const totalInput = document.querySelector('#id_total');
    const estadoPagoSelect = document.querySelector('#id_id_estado_pago');
    const cuotasInput = document.querySelector('#id_cuotas');  // <-- AQUI

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

    // ---- FUNCIÓN PARA HABILITAR/DESHABILITAR APORTES ----
    function actualizarHabilitadoAporte() {
        console.log("Ejecutando actualizarHabilitadoAporte()");
        console.log("Valor actual de cuotasInput.checked =", cuotasInput.checked);
        let totall=totalInput.value;

        if (cuotasInput.checked) {
            console.log("Cuotas activado  habilitando aporte");
            aporteInput.disabled = false;
            pagadoInput.disabled= true;
        } else {
            console.log("Cuotas desactivado  deshabilitando aporte");
            pagadoInput.value= totall;
            aporteInput.disabled = true;
            aporteInput.value = 0;
            actualizarPagado();
            console.log("total: "+totall)
        }
    }

    // Ejecutar inicial
    console.log("Llamando actualizarHabilitadoAporte() al cargar");
    actualizarHabilitadoAporte();

    // Vincular a cambios
    cuotasInput.addEventListener('change', actualizarHabilitadoAporte);

    // Guardar base original
    if (!pagadoInput.dataset.baseValue) {
        pagadoInput.dataset.baseValue = parseFloat(pagadoInput.value || 0);
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

        if (!isNaN(total) && !isNaN(pagado) && pagado >= total && estadoPagadoId) {
            nuevoValor = estadoPagadoId;
            mensajeColor = "green";
            mensajeTexto = `Pagado: L. ${pagado.toFixed(2)} (COMPLETO)`;
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

    

    function actualizarPagado() {
        const base = parseFloat(pagadoInput.dataset.baseValue || 0);
        const aporte = parseFloat(aporteInput.value || 0);
        const total = parseFloat(totalInput.value || 0);

        // Si aporte está deshabilitado, simplemente pagado = total
        if (aporteInput.disabled) {
            pagadoInput.value = total.toFixed(2);
        } else {
            const nuevoPagado = base + aporte;
            pagadoInput.value = nuevoPagado.toFixed(2);
        }

        actualizarEstadoPago(total, parseFloat(pagadoInput.value));
    }
    // Observar cambios en totalInput
    totalInput.addEventListener('totalActualizado', function() {
        console.log("Evento totalActualizado capturado");
        console.log("totalInput.value:", totalInput.value);
        console.log("aporteInput.disabled:", aporteInput.disabled);
        if (aporteInput.disabled) {
            console.log("Total actualizado por otro JS → actualizando pagado");
            actualizarPagado();
        }
    });





    aporteInput.addEventListener('input', function () {
        console.log("Evento input en aporte:", aporteInput.value);
        actualizarPagado();
    });

    console.log("Ejecutando actualizarPagado() inicial");
    actualizarPagado();

    
});
