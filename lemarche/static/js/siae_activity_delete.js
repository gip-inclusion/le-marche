document.addEventListener("DOMContentLoaded", function() {
    $('#siae_activity_delete_modal').on('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = $(event.relatedTarget);

        // Extract info from data-* attributes
        var siaeId = button.data('siae-id');
        var siaeSlug = button.data('siae-slug');
        var siaeActivityId = button.data('siae-activity-id');
        var siaeActivityNameDisplay = button.data('siae-activity-name-display');

        // Update the modal's content
        // - siae name display
        // - edit the form action url
        var modal = document.querySelector('#siae_activity_delete_modal');
        var modalForm = modal.querySelector('form');
        if (modal.querySelector('#siae-activity-name-display')) {
            modal.querySelector('#siae-activity-name-display').textContent = siaeActivityNameDisplay;
        }
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-activity-id-to-replace', siaeActivityId));
    });
});
