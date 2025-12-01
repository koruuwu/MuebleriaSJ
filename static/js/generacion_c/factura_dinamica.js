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
    console.log("[factura_dinamica] adminBase:", adminBase);

    async function obtenerEmpleado() {
        try {
            const r = await fetch(`${adminBase}obtener_empleado_logeado/`, {
                credentials: "same-origin"
            });
            if (!r.ok) return null;
            const data = await r.json();
            return data.id_empleado || null;
        } catch (err) {
            console.error("[factura_dinamica] Error obteniendo empleado:", err);
            return null;
        }
    }

    function conectarFactura() {
        const numeroFactura = document.querySelector("#id_id_factura, [name='id_factura']");
        if (!numeroFactura) return;

        async function generarFactura() {
            try {
                const r = await fetch(`${adminBase}generar_factura/`, {
                    credentials: "same-origin"
                });
                if (!r.ok) return;
                const data = await r.json();
                if (data.numero_factura) {
                    numeroFactura.value = data.numero_factura;
                    numeroFactura.dispatchEvent(new Event("input", { bubbles: true }));
                }
            } catch (err) {
                console.error("[factura_dinamica] Error generando factura:", err);
            }
        }

        // Generar automáticamente la factura al cargar
        if (!numeroFactura.dataset.loaded) {
            generarFactura();
            numeroFactura.dataset.loaded = true;
        }

        numeroFactura.setAttribute("readonly", true);
    }

    async function conectarEmpleado() {
        const campoEmpleado = document.querySelector("#id_id_empleado, [name='id_empleado']");
        if (!campoEmpleado) return;

        const empleadoId = await obtenerEmpleado();
        if (!empleadoId) return;

        console.log("ID Empleado obtenido:", empleadoId);

        // SOLUCIÓN: Usar solo readonly, no disabled
        campoEmpleado.value = empleadoId;

        //Actualizar visualmente el Select2
        $(campoEmpleado).val(empleadoId).trigger('change');

        //Bloquear edición pero permitir que Django lo envíe
        campoEmpleado.setAttribute("readonly", true);

        //Estilo para que parezca bloqueado
   

        // SOLUCIÓN: Eliminar el campo oculto para evitar duplicados
        const hiddenField = document.querySelector("#hidden_empleado");
        if (hiddenField) {
            hiddenField.remove();
        }

        console.log("Campo empleado configurado con valor:", campoEmpleado.value);
    }

    // Ejecutar al inicio
    conectarFactura();
    conectarEmpleado();

    // Reintento en Admin dinámico
    let tries = 0;
    const maxTries = 10;
    const retryInterval = setInterval(() => {
        tries++;
        conectarFactura();
        conectarEmpleado();
        if (tries >= maxTries) clearInterval(retryInterval);
    }, 400);

    // Observer para cambios
    const observer = new MutationObserver(() => {
        conectarFactura();
        conectarEmpleado();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("beforeunload", () => observer.disconnect());
});