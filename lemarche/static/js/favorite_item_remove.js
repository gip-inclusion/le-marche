document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('favorite_item_remove_modal').addEventListener('dsfr.disclose', (event) => {
        // Button that triggered the modal
        var button = event.explicitOriginalTarget;

        // Extract info from data-* attributes
        var siaeSlug = button.dataset["siaeSlug"];
        var siaeNameDisplay = button.dataset["siaeNameDisplay"];

        // Update the modal's content
        // - siae name display
        // - check favorite lists that already contain the siae
        // - edit the form action url
        var modal = document.querySelector('#favorite_item_remove_modal');
        var modalForm = modal.querySelector('form');
        if (modal.querySelector('#siae-name-display')) {
            modal.querySelector('#siae-name-display').textContent = siaeNameDisplay;
        }
        var formActionUrl = modalForm.getAttribute('data-action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug));
    });
});
