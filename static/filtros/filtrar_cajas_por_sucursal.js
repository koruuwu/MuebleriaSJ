document.addEventListener("DOMContentLoaded", function () {

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const adminIndex = parts.indexOf("admin");

        if (adminIndex === -1) return "/admin/";

        const baseParts = parts.slice(0, adminIndex + 3); // admin/auth/user
        return "/" + baseParts.join("/") + "/";
    }

    const adminBase = getAdminBaseUrl();
    console.log("Admin Base:", adminBase);

    const sucursalField = document.querySelector("select[name$='sucursal']");
    const cajaField = document.querySelector("select[name$='caja']");

    console.log("Sucursal Field:", sucursalField);
    console.log("Caja Field:", cajaField);


    if (!sucursalField || !cajaField) return;

    function triggerSelect2(el) {
        if (window.jQuery && window.jQuery.fn.select2) {
            try { window.jQuery(el).trigger("change.select2"); } catch(e) {}
        }
    }

    function actualizarCajas(cajas, prevValue = null) {
        if (!Array.isArray(cajas)) cajas = [];

        cajaField.innerHTML = '<option value="">---------</option>';
        cajas.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.nombre || (c.nombre_caja || c.label) || String(c.id);
            cajaField.appendChild(opt);
        });

        if (prevValue) {
            const exists = Array.from(cajaField.options).some(o => o.value == prevValue);
            cajaField.value = exists ? prevValue : "";
        }

        triggerSelect2(cajaField);
    }

    async function filtrarCajasPorSucursal(sucursalId) {
        if (!sucursalId) {
            actualizarCajas([]);
            return;
        }

        const prev = cajaField.value;

        cajaField.disabled = true;
        cajaField.innerHTML = '<option>Cargando...</option>';

        const url = `${adminBase}filtrar_cajas_por_sucursal/${sucursalId}/`;

        try {
            const resp = await fetch(url, { credentials: "same-origin" });

            if (!resp.ok) {
                actualizarCajas([]);
                return;
            }

            const data = await resp.json();
            actualizarCajas(data, prev);

        } catch (err) {
            console.error("Error AJAX cajas:", err);
            actualizarCajas([]);
        } finally {
            cajaField.disabled = false;
        }
    }

    // Eventos select2 o normales
    if (window.jQuery && window.jQuery.fn.select2) {
        window.jQuery(sucursalField).on(
            "select2:select select2:close change",
            function () {
                setTimeout(() => filtrarCajasPorSucursal(this.value), 10);
            }
        );
    } else {
        sucursalField.addEventListener("change", function () {
            filtrarCajasPorSucursal(this.value);
        });
    }

    // Inicializar si ya hay sucursal escogida
    if (sucursalField.value) {
        filtrarCajasPorSucursal(sucursalField.value);
    }
});
