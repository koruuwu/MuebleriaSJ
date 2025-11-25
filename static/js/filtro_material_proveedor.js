document.addEventListener("DOMContentLoaded", function () {

    function getAdminBaseUrl() {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const adminIndex = parts.indexOf("admin");

        if (adminIndex === -1) return "/admin/";

        const baseParts = parts.slice(0, adminIndex + 3);
        return "/" + baseParts.join("/") + "/";
    }

    const adminBase = getAdminBaseUrl();
    console.log("Admin Base:", adminBase);

    function conectarFila(fila) {
        const materialSelect = fila.querySelector('select[name$="material"]');
        const proveedorSelect = fila.querySelector('select[name$="proveedor"]');

        if (!materialSelect || !proveedorSelect) return;

        function actualizarProveedores() {
            const materialId = materialSelect.value;
            const url = materialId
                ? `${adminBase}filtrar_proveedores/${materialId}/`
                : `${adminBase}filtrar_proveedores/0/`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    const currentValue = proveedorSelect.value; // guardamos el valor seleccionado
                    proveedorSelect.innerHTML = '<option value="">---------</option>';
                    data.forEach(item => {
                        proveedorSelect.innerHTML += `<option value="${item.id}">${item.compañia}</option>`;
                    });
                    // restaurar el valor seleccionado si existe
                    if (currentValue) proveedorSelect.value = currentValue;

                    if (window.jQuery && window.jQuery.fn.select2) {
                        window.jQuery(proveedorSelect).trigger("change.select2");
                    }
                });
        }

        function actualizarMateriales() {
            const proveedorId = proveedorSelect.value;
            const url = proveedorId
                ? `${adminBase}filtrar_materiales/${proveedorId}/`
                : `${adminBase}filtrar_materiales/0/`;

            fetch(url)
                .then(r => r.json())
                .then(data => {
                    const currentValue = materialSelect.value; // guardamos el valor seleccionado
                    materialSelect.innerHTML = '<option value="">---------</option>';
                    data.forEach(item => {
                        materialSelect.innerHTML += `<option value="${item.id}">${item.nombre}</option>`;
                    });
                    // restaurar el valor seleccionado si existe
                    if (currentValue) materialSelect.value = currentValue;

                    if (window.jQuery && window.jQuery.fn.select2) {
                        window.jQuery(materialSelect).trigger("change.select2");
                    }
                });
        }

        materialSelect.addEventListener("change", actualizarProveedores);
        proveedorSelect.addEventListener("change", actualizarMateriales);

        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(materialSelect).on("select2:select select2:close change", () =>
                setTimeout(actualizarProveedores, 10)
            );
            window.jQuery(proveedorSelect).on("select2:select select2:close change", () =>
                setTimeout(actualizarMateriales, 10)
            );
        }
    }

    document.querySelectorAll(".inline-related fieldset").forEach(conectarFila);
    document.body.addEventListener("formset:added", e => conectarFila(e.target));

});
