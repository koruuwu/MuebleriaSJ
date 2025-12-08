// static/js/filtros/filtro_orden_aportaciones.js
document.addEventListener("DOMContentLoaded", function () {
    console.log("JS cargado correctamente");

    const ordenSelect = document.getElementById("id_orden_selector");
    const detalleSelect = document.getElementById("id_id_orden_detalle");
    const helpText = document.getElementById("detalle_helptext");

    if (!ordenSelect || !detalleSelect) {
        console.error("No se encontraron los selects");
        return;
    }

    function setHelpText(mueble, plan) {
        if (helpText) {
            if (mueble && plan !== undefined && plan !== null && plan !== "") {
                helpText.innerHTML = `Para <strong>${mueble}</strong> el plan es de <strong>${plan}</strong> unidades.`;
            } else {
                helpText.innerHTML = "Seleccione un detalle para ver información.";
            }
        }
    }

    function updateHelpTextFromSelected() {
        const selectedOption = detalleSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value) {
            const mueble = selectedOption.dataset.mueble;
            const plan = selectedOption.dataset.plan;

            // Si ya tenemos los data-* usamos directo
            if (mueble !== undefined && plan !== undefined) {
                setHelpText(mueble, plan);
                return;
            }

            // Si no tenemos los data-* pero hay orden, intentar recuperarlos vía fetch
            const ordenId = ordenSelect.value;
            if (ordenId) {
                console.log("No hay data-* en la opción seleccionada. Solicitando datos del servidor...");
                const url = `/admin/Trabajo/aportacionempleado/filtrar_detalles/${ordenId}/`;
                fetch(url)
                    .then(resp => {
                        if (!resp.ok) throw new Error("Respuesta no OK: " + resp.status);
                        return resp.json();
                    })
                    .then(data => {
                        // buscar el elemento correspondiente y anotar data-* en la opción ya renderizada
                        const selVal = selectedOption.value;
                        const match = (data || []).find(it => String(it.id) === String(selVal));
                        if (match) {
                            selectedOption.dataset.mueble = match.mueble;
                            selectedOption.dataset.plan = match.plan;
                            setHelpText(match.mueble, match.plan);
                            console.log("Atribuidos data-* a la opción seleccionada desde servidor:", match);
                        } else {
                            console.warn("No se encontró el detalle seleccionado en la respuesta del servidor.");
                            setHelpText(null, null);
                        }
                    })
                    .catch(err => {
                        console.error("Error al obtener detalles para el helptext:", err);
                        setHelpText(null, null);
                    });
                return;
            }

            // Si no hay orden para consultar, mostrar placeholder
            setHelpText(null, null);
        } else {
            setHelpText(null, null);
        }
    }

    function initSelect2Listener() {
        if (!window.jQuery || !jQuery.fn.select2) {
            console.log("Select2 aún no está listo, reintentando...");
            return setTimeout(initSelect2Listener, 100);
        }

        console.log("Select2 LISTO");

        // Cuando se selecciona una orden -> cargar sus detalles
        jQuery(ordenSelect).on("select2:select", function () {
            const ordenId = this.value;
            detalleSelect.innerHTML = "<option value=''>Cargando...</option>";
            if (helpText) helpText.innerHTML = "Cargando detalles…";

            const url = `/admin/Trabajo/aportacionempleado/filtrar_detalles/${ordenId}/`;
            fetch(url)
                .then(response => {
                    if (!response.ok) throw new Error("Respuesta no OK: " + response.status);
                    return response.json();
                })
                .then(data => {
                    detalleSelect.innerHTML = "";

                    // Opción vacía inicial (placeholder)
                    const emptyOption = document.createElement("option");
                    emptyOption.value = "";
                    emptyOption.textContent = "Seleccione un detalle…";
                    emptyOption.disabled = true;
                    emptyOption.selected = true;
                    detalleSelect.appendChild(emptyOption);

                    data.forEach(item => {
                        const option = document.createElement("option");
                        option.value = item.id;
                        option.textContent = item.texto;
                        option.dataset.mueble = item.mueble;
                        option.dataset.plan = item.plan;
                        detalleSelect.appendChild(option);
                    });

                    // Asegurar que quede sin selección
                    detalleSelect.value = "";
                    jQuery(detalleSelect).trigger("change.select2");

                    // Help text por defecto
                    setHelpText(null, null);
                })
                .catch(err => {
                    console.error("Error cargando detalles:", err);
                    detalleSelect.innerHTML = "<option value=''>Error cargando detalles</option>";
                    jQuery(detalleSelect).trigger("change.select2");
                    setHelpText(null, null);
                });
        });

        // Cuando se selecciona un detalle -> actualizar help text (ya tendrán data-* si vinieron del fetch)
        jQuery(detalleSelect).on("select2:select", function (e) {
            const selectedOption = e.params.data && e.params.data.element ? e.params.data.element : detalleSelect.selectedOptions[0];
            if (!selectedOption) {
                setHelpText(null, null);
                return;
            }
            const mueble = selectedOption.dataset.mueble;
            const plan = selectedOption.dataset.plan;
            setHelpText(mueble, plan);
        });

        // --- Al cargar, si ya hay un detalle seleccionado (edición), asegurarnos de tener los data-* y actualizar helptext ---
        // Si la opción seleccionada no tiene data-* intentamos obtenerlos desde el endpoint por la orden actual
        updateHelpTextFromSelected();
    }

    initSelect2Listener();
});
