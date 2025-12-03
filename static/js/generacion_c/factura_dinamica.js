document.addEventListener("DOMContentLoaded", function () {
    console.log("[factura_dinamica] DOM listo");

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const adminIndex = parts.indexOf("admin");
        if (adminIndex === -1) return "/admin/";
        const slice = parts.slice(adminIndex, adminIndex + 3);
        return "/" + slice.join("/") + "/";
    }

    const adminBase = getAdminBaseUrl();

    // Cache interno para no llamar varias veces
    let empleadoCached = null;

    async function obtenerEmpleado() {
        if (empleadoCached !== null) return empleadoCached;

        try {
            const r = await fetch(`${adminBase}obtener_empleado_logeado/`, {
                credentials: "same-origin"
            });
            if (!r.ok) return null;
            const data = await r.json();
            empleadoCached = data.id_empleado || null;
            return empleadoCached;
        } catch (err) {
            console.error("[factura_dinamica] Error obteniendo empleado:", err);
            return null;
        }
    }

    async function conectarEmpleado() {
        const campoEmpleado = document.querySelector("#id_id_empleado, [name='id_empleado']");
        if (!campoEmpleado) return;

        // Evitar volver a asignar
        if (campoEmpleado.dataset.empleadoLoaded === "1") return;

        const empleadoId = await obtenerEmpleado();
        if (!empleadoId) return;

        campoEmpleado.value = empleadoId;
        if (typeof $ !== "undefined" && $(campoEmpleado).trigger) {
            $(campoEmpleado).val(empleadoId).trigger('change');
        }

        campoEmpleado.setAttribute("readonly", true);
        campoEmpleado.dataset.empleadoLoaded = "1";

        // Quitar hidden duplicado si existe
        const hiddenField = document.querySelector("#hidden_empleado");
        if (hiddenField) hiddenField.remove();

        console.info("[factura_dinamica] Campo empleado configurado con valor:", empleadoId);
    }

    /*async function conectarFactura() {
        const numeroFactura = document.querySelector("#id_id_factura, [name='id_factura']");
        if (!numeroFactura) return;

        // SI YA TIENE VALOR → estamos editando → NO GENERAR
        if (numeroFactura.value && numeroFactura.value.trim() !== "") {
            numeroFactura.setAttribute("readonly", true);
            numeroFactura.dataset.facturaLoaded = "1";
            return;
        }

        // SI NO TIENE VALOR → SOLO AHÍ GENERAMOS
        try {
            const r = await fetch(`${adminBase}generar_factura/`, { credentials: "same-origin" });
            if (!r.ok) return;

            const data = await r.json();
            if (data.numero_factura) {
                numeroFactura.value = data.numero_factura;
                numeroFactura.dispatchEvent(new Event("input", { bubbles: true }));
                numeroFactura.setAttribute("readonly", true);
                numeroFactura.dataset.facturaLoaded = "1";
            }
        } catch (err) {
            console.error("[factura_dinamica] Error generando factura:", err);
        }
    }*/



    // Ejecutar al cargar
    conectarEmpleado();
    //conectarFactura();
});
