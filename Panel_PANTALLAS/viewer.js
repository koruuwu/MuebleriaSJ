
document.addEventListener("DOMContentLoaded", () => {
    const contentArea = document.getElementById("content-area");
    const breadcrumb = document.getElementById("breadcrumb");

    // -----------------------------
    // Delegación de clicks: navegación
    // -----------------------------
    document.body.addEventListener("click", async (e) => {
        const link = e.target.closest(".nav-link, .action-card");
        if (!link) return;
        e.preventDefault();

        // Actualiza activo
        document.querySelectorAll(".nav-link, .action-card").forEach(l => l.classList.remove("active"));
        link.classList.add("active");

        const pageUrl = link.getAttribute("data-page");
        if (!pageUrl) return;

        breadcrumb.textContent = link.textContent.trim();

        try {
            const response = await fetch(pageUrl);
            const html = await response.text();
            contentArea.innerHTML = html;
        } catch (err) {
            contentArea.innerHTML = `<div class="alert alert-danger">Error al cargar ${pageUrl}</div>`;
        }
    });

    // Delegación universal de submit
    document.body.addEventListener("submit", (e) => {
        const form = e.target;
        if (!form.matches("form")) return;

        e.preventDefault(); // evita recarga

        const formData = new FormData(form);
        const datos = {};
        for (let [k, v] of formData.entries()) datos[k] = v;

        // Mostrar mensaje universal
        mostrarMensaje(`✅ Formulario "${form.id}" enviado localmente:\n` + JSON.stringify(datos, null, 2), true);

        // Deshabilitar botón
        const btn = form.querySelector('button[type="submit"]');
        if (btn) btn.disabled = true;

        // -----------------------
        // Si es form-usuario, crea el formulario especial
        // -----------------------
        if (form.id === "form-usuario") {
            const tipo = datos.tipo;
            const idUsuario = datos.id_usuario;
            cargarFormularioEspecial(idUsuario, tipo);
        }
    });


    // -----------------------------
    // Función para mensajes
    // -----------------------------
    function mostrarMensaje(msg, exito = true) {
        let div = document.getElementById("mensaje");
        if (!div) {
            div = document.createElement("div");
            div.id = "mensaje";
            contentArea.prepend(div);
        }
        div.innerHTML = `<pre>${msg}</pre>`;
        div.className = exito ? "alert alert-success" : "alert alert-danger";
        div.style.display = "block";
    }
});
