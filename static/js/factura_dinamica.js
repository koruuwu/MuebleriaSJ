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

   function conectarFactura() {
    const empleado = document.querySelector("[name='id_id_empleado'], [name='id_empleado']");
    const caja = document.querySelector("#id_id_caja, [name='caja']");
    const numeroFactura = document.querySelector("#id_id_factura, [name='id_factura']");

    if (!empleado || !caja || !numeroFactura) return;

    async function generarFactura() {
        const empleadoId = empleado.value;
        const cajaId = caja.value;
        if (!empleadoId || !cajaId) return;

        try {
            const r = await fetch(`${adminBase}generar_factura/${empleadoId}/${cajaId}/`, {
                credentials: "same-origin"
            });
            if (!r.ok) return;
            const data = await r.json();
            if (data.numero_factura) {
                numeroFactura.value = data.numero_factura;
                numeroFactura.dispatchEvent(new Event("input", { bubbles: true }));
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Solo agregar listeners una vez
    if (!empleado.dataset.listener) {
        empleado.addEventListener("change", generarFactura);
        empleado.dataset.listener = true;
    }
    if (!caja.dataset.listener) {
        caja.addEventListener("change", generarFactura);
        caja.dataset.listener = true;
    }

    // select2
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
        if (!empleado.dataset.select2) {
            window.jQuery(empleado).on("select2:select select2:close change", generarFactura);
            empleado.dataset.select2 = true;
        }
        if (!caja.dataset.select2) {
            window.jQuery(caja).on("select2:select select2:close change", generarFactura);
            caja.dataset.select2 = true;
        }
    }
 }


    // Conectar inmediatamente
    conectarFactura();

    // Reintentos para cuando Admin renderiza dinámicamente
    let tries = 0;
    const maxTries = 10;
    const interval = 400;
    const retryInterval = setInterval(() => {
        tries++;
        conectarFactura();
        if (tries >= maxTries) clearInterval(retryInterval);
    }, interval);

    // MutationObserver por si el admin reemplaza selects
    const observer = new MutationObserver(() => conectarFactura());
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
    window.addEventListener("beforeunload", () => observer.disconnect());
});
