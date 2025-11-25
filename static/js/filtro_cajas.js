document.addEventListener("DOMContentLoaded", function () {

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const adminIndex = parts.indexOf("admin");
        if (adminIndex === -1) return "/admin/";
        const baseParts = parts.slice(0, adminIndex + 3); // admin/app/model
        return "/" + baseParts.join("/") + "/";
    }

    const adminBase = getAdminBaseUrl();
    console.log("Admin Base:", adminBase);

    const empleadoField = document.getElementById("id_id_empleado");
    const cajaField = document.getElementById("id_caja");
    if (!empleadoField || !cajaField) return;

    function triggerSelect2(el) {
        if (window.jQuery && window.jQuery.fn.select2) {
            try { window.jQuery(el).trigger("change.select2"); } catch(e) { /* ignore */ }
        }
    }

    function actualizarCajas(cajas, prevValue=null) {
        // si cajas es null o no es array -> limpiar
        if (!Array.isArray(cajas)) cajas = [];

        cajaField.innerHTML = '<option value="">---------</option>';
        cajas.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.nombre || (c.nombre_caja || c.label) || String(c.id);
            cajaField.appendChild(opt);
        });

        // mantener prevValue si existe en la nueva lista
        if (prevValue) {
            const exists = Array.from(cajaField.options).some(o => o.value == prevValue);
            if (exists) cajaField.value = prevValue;
            else cajaField.value = ""; // limpia si ya no existe
        }

        triggerSelect2(cajaField);
    }

    async function filtrarCajasPorEmpleado(empleadoId) {
        // limpiar si no hay empleado
        if (!empleadoId) {
            actualizarCajas([]);
            return;
        }

        const prev = cajaField.value;
        cajaField.disabled = true;
        cajaField.innerHTML = '<option value="">Cargando...</option>';

        const url = `${adminBase}filtrar_cajas/${empleadoId}/`;
        console.log("Fetch cajas ->", url);

        try {
            const resp = await fetch(url, { credentials: 'same-origin' });

            // status check
            if (!resp.ok) {
                const txt = await resp.text().catch(()=>"(no body)");
                console.error("fetch error status", resp.status, txt);
                actualizarCajas([]);
                return;
            }

            const contentType = (resp.headers.get("content-type") || "").toLowerCase();
            if (!contentType.includes("application/json")) {
                // mostrar el body para debugging (puede ser HTML de login o traceback)
                const text = await resp.text().catch(()=>"(no body)");
                console.error("Respuesta no JSON:", text);
                actualizarCajas([]);
                return;
            }

            const data = await resp.json();
            // data expected: array [{id:, nombre:}, ...]
            actualizarCajas(data, prev);

        } catch (err) {
            console.error("Error AJAX cajas:", err);
            actualizarCajas([]);
        } finally {
            cajaField.disabled = false;
        }
    }

    // Eventos (compatible con select2)
    if (window.jQuery && window.jQuery.fn.select2) {
        // manejar select2 events + fallback change
        window.jQuery(empleadoField).on("select2:select select2:close change", function () {
            // select2 a veces dispara sync/async, dejar un micro-delay
            setTimeout(() => filtrarCajasPorEmpleado(this.value), 10);
        });
    } else {
        empleadoField.addEventListener("change", function () {
            filtrarCajasPorEmpleado(this.value);
        });
    }

    // inicializar al cargar si ya hay empleado seleccionado
    if (empleadoField.value) {
        filtrarCajasPorEmpleado(empleadoField.value);
    }

});
