document.addEventListener("DOMContentLoaded", function() {
    $('#user_request_confirm_modal').on('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = $(event.relatedTarget);

        // Extract info from data-* attributes
        // var siaeId = button.data('siae-id');
        var siaeSlug = button.data('siae-slug');
        var initiatorFullName = button.data('initiator-full-name');
        var siaeUserRequestId = button.data('siae-user-request-id');

        // Update the modal's content
        // - siae user full name
        // - edit the form action url
        var modal = document.querySelector('#user_request_confirm_modal');
        modal.querySelector('#initiator-full-name-to-replace').textContent = initiatorFullName;
        var modalForm = modal.querySelector('form');
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-user-request-id-to-replace', siaeUserRequestId));
    });

    $('#user_request_cancel_modal').on('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = $(event.relatedTarget);

        // Extract info from data-* attributes
        // var siaeId = button.data('siae-id');
        var siaeSlug = button.data('siae-slug');
        var initiatorFullName = button.data('initiator-full-name');
        var siaeUserRequestId = button.data('siae-user-request-id');

        // Update the modal's content
        // - siae user full name
        // - edit the form action url
        var modal = document.querySelector('#user_request_cancel_modal');
        modal.querySelector('#initiator-full-name-to-replace').textContent = initiatorFullName;
        var modalForm = modal.querySelector('form');
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-user-request-id-to-replace', siaeUserRequestId));
    });
});
