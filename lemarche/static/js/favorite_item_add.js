document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('favorite_item_add_modal').addEventListener('dsfr.disclose', (event) => {
        // Button that triggered the modal
        var button = event.explicitOriginalTarget;

        // Extract info from data-* attributes
        var siaeSlug = button.dataset["siaeSlug"];
        var siaeNameDisplay = button.dataset["siaeNameDisplay"];
        // Button that triggered the modal
        var button = $(event.relatedTarget);

        // Update the modal's content
        // - siae name display
        // - check favorite lists that already contain the siae
        // - edit the form action url
        var modal = document.querySelector('#favorite_item_add_modal');
        var modalForms = modal.querySelectorAll('form');
        if (modal.querySelector('#siae-name-display')) {
            modal.querySelector('#siae-name-display').textContent = siaeNameDisplay;
        }
        modalForms.forEach(form => {
            var formActionUrl = form.getAttribute('data-action');
            form.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug));
        });
    });
});
