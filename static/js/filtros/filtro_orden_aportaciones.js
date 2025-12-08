document.addEventListener("DOMContentLoaded", function () {
    console.log("JS cargado correctamente");

    const ordenSelect = document.getElementById("id_orden_selector");
    const detalleSelect = document.getElementById("id_id_orden_detalle");
    const helpText = document.getElementById("detalle_helptext");

    if (!ordenSelect || !detalleSelect) {
        console.error("No se encontraron los selects");
        return;
    }

    function initSelect2Listener() {
        if (!window.jQuery || !jQuery.fn.select2) {
            console.log("Select2 aún no está listo, reintentando...");
            return setTimeout(initSelect2Listener, 100);
        }

        console.log("Select2 LISTO");

        jQuery(ordenSelect).on("select2:select", function () {
            const ordenId = this.value;

            console.log("Orden seleccionada:", ordenId);

            detalleSelect.innerHTML = "<option>Cargando...</option>";
            if (helpText) helpText.innerHTML = "Cargando detalles…";

            const url = `/admin/Trabajo/aportacionempleado/filtrar_detalles/${ordenId}/`;
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    detalleSelect.innerHTML = "";

                    // ❌ Opción vacía inicial
                    const emptyOption = document.createElement("option");
                    emptyOption.value = "";
                    emptyOption.textContent = "Seleccione un detalle…";
                    detalleSelect.appendChild(emptyOption);

                    data.forEach(item => {
                        const option = document.createElement("option");
                        option.value = item.id;
                        option.textContent = item.texto;
                        option.dataset.mueble = item.mueble;
                        option.dataset.plan = item.plan;
                        detalleSelect.appendChild(option);
                    });

                    // Limpiar selección anterior
                    detalleSelect.value = "";

                    // Actualizar Select2
                    jQuery(detalleSelect).trigger("change.select2");

                    if (helpText)
                        helpText.innerHTML = "Seleccione un detalle para ver información.";
                });

        });

        // Cuando el usuario selecciona el detalle -> actualizar help text
        jQuery(detalleSelect).on("select2:select", function (e) {
            const selected = e.params.data.element;

            if (!selected) return;

            const mueble = selected.dataset.mueble;
            const plan = selected.dataset.plan;

            if (helpText) {
                helpText.innerHTML =
                    `Para <strong>${mueble}</strong> el plan es de <strong>${plan}</strong> unidades.`;
            }
        });
    }

    initSelect2Listener();
});
