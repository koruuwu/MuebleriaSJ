console.log("JS de aporte cargado");

document.addEventListener("DOMContentLoaded", function () {
    const isOrdenesVentaPage = window.location.pathname.includes('/ordenesventa/');
    if (!isOrdenesVentaPage) return;

    const aporteInput = document.querySelector('#id_aporte');
    const pagadoInput = document.querySelector('#id_pagado');
    const totalInput = document.querySelector('#id_total');
    const estadoPagoSelect = document.querySelector('#id_id_estado_pago');

    if (!aporteInput || !pagadoInput || !totalInput || !estadoPagoSelect) return;

    // Guardar base original del pagado
    if (!pagadoInput.dataset.baseValue) {
        pagadoInput.dataset.baseValue = parseFloat(pagadoInput.value || 0);
    }

    // Crear mensaje debajo del pagado
    let mensaje = document.querySelector('#mensaje-pagado');
    if (!mensaje) {
        mensaje = document.createElement('small');
        mensaje.id = "mensaje-pagado";
        mensaje.style.display = 'block';
        mensaje.style.fontSize = '12px';
        mensaje.style.fontWeight = 'bold';
        mensaje.style.marginTop = '4px';
        pagadoInput.insertAdjacentElement("afterend", mensaje);
    }

    function actualizarEstadoPago(total, pagado) {
        if (!estadoPagoSelect) return;

        let estadoPagadoId = null;
        let estadoPendienteId = null;

        // Buscar IDs de las opciones del select
        [...estadoPagoSelect.options].forEach(opt => {
            const texto = opt.textContent.trim().toLowerCase();
            if (texto === "pagado") estadoPagadoId = opt.value;
            if (texto === "pendiente") estadoPendienteId = opt.value;
        });

        if (pagado >= total && estadoPagadoId) {
            estadoPagoSelect.value = estadoPagadoId;
            mensaje.style.color = "green";
            mensaje.textContent = `Pagado: L. ${pagado.toFixed(2)} (COMPLETO)`;
        } else if (estadoPendienteId) {
            estadoPagoSelect.value = estadoPendienteId;
            mensaje.style.color = "red";
            mensaje.textContent = `Pagado: L. ${pagado.toFixed(2)} (PENDIENTE)`;
        }
    }

    function actualizarPagado() {
        const base = parseFloat(pagadoInput.dataset.baseValue || 0);
        const aporte = parseFloat(aporteInput.value || 0);
        const total = parseFloat(totalInput.value || 0);
        const nuevoPagado = base + aporte;

        pagadoInput.value = nuevoPagado.toFixed(2);

        actualizarEstadoPago(total, nuevoPagado);
    }

    aporteInput.addEventListener('input', actualizarPagado);
    actualizarPagado();

    // Reset al guardar
    document.querySelectorAll('input[name="_save"], input[name="_continue"], input[name="_addanother"]').forEach(btn => {
        btn.addEventListener('click', function () {
            aporteInput.value = 0;
            pagadoInput.dataset.baseValue = pagadoInput.value;
        });
    });
});
