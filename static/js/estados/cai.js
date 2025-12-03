console.log("cai.js cargado");

function parseFechaDDMMYYYY(fechaStr) {
    const partes = fechaStr.split("/");
    if (partes.length !== 3) return null;
    const dia = parseInt(partes[0], 10);
    const mes = parseInt(partes[1], 10) - 1; // JS meses 0-11
    const anio = parseInt(partes[2], 10);
    return new Date(anio, mes, dia);
}


function evaluarActivo(form) {
    const fechaVencInput = form.querySelector('[name$="fecha_vencimiento"]');
    const ultimaSecInput = form.querySelector('[name$="ultima_secuencia"]');
    const rangoFinalInput = form.querySelector('[name$="rango_final"]');
    const activoInput = form.querySelector('[name$="activo"]');

    if (!fechaVencInput || !ultimaSecInput || !rangoFinalInput || !activoInput) return;

    let activo = true;

 

    const fechaVenc = parseFechaDDMMYYYY(fechaVencInput.value);
    fechaVenc.setHours(0,0,0,0);

    const hoy = new Date();
    hoy.setHours(0,0,0,0);
    console.log("fecha de hoy "+hoy)

    if (fechaVencInput.value && fechaVenc <= hoy) {
        activo = false;
        console.log(`CAI "${form.querySelector('[name$="codigo_cai"]').value}" inactivo: fecha vencida (${fechaVencInput.value})`);
    }


    // --- Desactivar por secuencia agotada ---
    const ultima = parseInt(ultimaSecInput.value || "0");
    const final = parseInt(rangoFinalInput.value || "0");
    if (!isNaN(ultima) && !isNaN(final) && ultima >= final) {
        activo = false;
        console.log(`CAI "${form.querySelector('[name$="codigo_cai"]').value}" inactivo: secuencia alcanzó el rango final (${ultima} >= ${final})`);
    }

    activoInput.checked = activo;
}

// Función para inicializar los inlines existentes y nuevos
function initInlines() {
    const inlines = document.querySelectorAll('.dynamic-cai_set');
    //console.log("Inlines detectados:", inlines);

    inlines.forEach(form => {
        if (form.dataset.activado) return;
        form.dataset.activado = "true";

        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener("input", () => evaluarActivo(form));
        });

        evaluarActivo(form);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    initInlines();

    const group = document.getElementById("cai_set-group");
    if (group) {
        const observer = new MutationObserver(() => initInlines());
        observer.observe(group, { childList: true, subtree: true });
    }
});
