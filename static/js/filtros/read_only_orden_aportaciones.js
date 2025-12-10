console.log("JS de aporte cargado (inicio)");

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOMContentLoaded disparado");

    const ordenDetalleSelect = $('#id_id_orden_detalle');
    const ordenSelectorSelect = $('#id_orden_selector');
    const cantidadSolicitadaInput = document.querySelector('#id_cantidad_solicitada');
    const cantAprobadaInput = document.querySelector('#id_cant_aprobada');
    const cantidadFinalizadaInput = document.querySelector('#id_cantidad_finalizada');
    const estadoInput = document.querySelector('#id_estado');


    const campos = [
        cantidadSolicitadaInput,
        cantAprobadaInput,
        cantidadFinalizadaInput,
        estadoInput
    ];
    cantAprobadaInput.readOnly = true;
    cantidadFinalizadaInput.readOnly = true;

  

    actualizarEstiloReadonly() 

    function actualizarEstiloReadonly() {
        campos.forEach(campo => {
            if (!campo) return;
            if (campo.readOnly) {
                campo.style.backgroundColor = "#f0f0f0";
                campo.style.color = "#999";
            } else {
                campo.style.backgroundColor = "";
                campo.style.color = "";
            }
        });

        [ordenDetalleSelect, ordenSelectorSelect].forEach(select => {
            if (!select.length) return;
            const isReadonly = select.data('readonly');
            const container = select.next('.select2-container');

            if (isReadonly) {
                container.css({"background-color": "#f0f0f0", "color": "#999"});
            } else {
                container.css({"background-color": "", "color": ""});
            }
        });
    }

    function aplicarReadonlySegunEstado() {
        const cantAprobada = parseInt(cantAprobadaInput?.value || 0);
        const cantfin = parseInt(cantidadFinalizadaInput?.value || 0);
        const estado = estadoInput?.value;

        console.log(`Aplicando readonly → cantAprobada=${cantAprobada}, estado=${estado}`);

        // Inputs normales
        if (cantAprobada > 0 || estado === 'COMP') {
            cantidadSolicitadaInput.readOnly = true;
            cantidadFinalizadaInput.readOnly = true;
            cantAprobadaInput.readOnly = true;
        }
     

        // Select2
        const readonlySelect = (cantAprobada > 0 || estado === 'COMP');
        ordenDetalleSelect.data('readonly', readonlySelect);
        ordenSelectorSelect.data('readonly', readonlySelect);

        // Bloqueo real de Select2
        [ordenDetalleSelect, ordenSelectorSelect].forEach(select => {
            select.off('select2:opening').on('select2:opening', function(e){
                if (select.data('readonly')) {
                    e.preventDefault();
                    console.log(`Select2 ${select.attr('id')} bloqueado`);
                }
            });
        });

        actualizarEstiloReadonly();
    }

    aplicarReadonlySegunEstado();

    if (estadoInput) {
        estadoInput.addEventListener("change", function() {
            console.log("Evento change en estado");
            aplicarReadonlySegunEstado();
        });
    }

    console.log("JS de aporte finalizado correctamente.");
});
