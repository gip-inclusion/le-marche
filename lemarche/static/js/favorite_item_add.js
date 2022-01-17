document.addEventListener("DOMContentLoaded", function() {
    $('#favorite_item_add_modal').on('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = $(event.relatedTarget);

        // Extract info from data-* attributes
        var siaeId = button.data('siae-id');
        var siaeSlug = button.data('siae-slug');
        var siaeNameDisplay = button.data('siae-name-display');

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
            var formActionUrl = form.getAttribute('action');
            form.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug));
        });
    });
});
