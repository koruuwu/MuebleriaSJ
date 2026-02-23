(function () {

    function insertSelectAll(inline) {
        if (inline.querySelector('.select-all-calificaciones')) return;

        const checkboxes = inline.querySelectorAll(
            'input[type="checkbox"][name$="-DELETE"]'
        );

        if (!checkboxes.length) return;

        const container = document.createElement('div');
        container.className = 'select-all-calificaciones';
        container.style.margin = '10px 0';
        container.style.fontWeight = 'bold';

        const selectAll = document.createElement('input');
        selectAll.type = 'checkbox';
        selectAll.style.marginRight = '6px';

        selectAll.addEventListener('change', function () {
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
        });

        container.appendChild(selectAll);
        container.appendChild(
            document.createTextNode(' Seleccionar todas las calificaciones a eliminar')
        );

        inline.prepend(container);
    }

    function watchForInline() {
        const observer = new MutationObserver(() => {
            document.querySelectorAll('.inline-group').forEach(insertSelectAll);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    document.addEventListener('DOMContentLoaded', watchForInline);

})();
