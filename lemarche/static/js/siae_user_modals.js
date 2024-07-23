document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('siae_user_request_confirm_modal').addEventListener('dsfr.disclose', (event) => {
        // Button that triggered the modal
        var button = event.explicitOriginalTarget;
        var siaeSlug = button.dataset["siaeSlug"];
        var initiatorFullName = button.dataset["initiatorFullName"];
        var siaeUserRequestId = button.dataset["siaeUserRequestId"];

        // Update the modal's content
        // - siae user full name
        // - edit the form action url
        var modal = document.querySelector('#siae_user_request_confirm_modal');
        modal.querySelector('#initiator-full-name-to-replace').textContent = initiatorFullName;
        var modalForm = modal.querySelector('form');
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-user-request-id-to-replace', siaeUserRequestId));
    });

    document.getElementById('siae_user_request_cancel_modal').addEventListener('dsfr.disclose', (event) => {
        // Button that triggered the modal
        var button = event.explicitOriginalTarget;
        var siaeSlug = button.dataset["siaeSlug"];
        var initiatorFullName = button.dataset["initiatorFullName"];
        var siaeUserRequestId = button.dataset["siaeUserRequestId"];

        // Update the modal's content
        // - siae user full name
        // - edit the form action url
        var modal = document.querySelector('#siae_user_request_cancel_modal');
        modal.querySelector('#initiator-full-name-to-replace').textContent = initiatorFullName;
        var modalForm = modal.querySelector('form');
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-user-request-id-to-replace', siaeUserRequestId));
    });

    document.getElementById('siae_user_delete_modal').addEventListener('dsfr.disclose', (event) => {
        // Button that triggered the modal
        var button = event.explicitOriginalTarget;
        var siaeSlug = button.dataset["siaeSlug"];
        var userFullName = button.dataset["userFullName"];
        var siaeUserId = button.dataset["siaeUserId"];

        // Update the modal's content
        // - siae user full name
        // - edit the form action url
        var modal = document.querySelector('#siae_user_delete_modal');
        modal.querySelector('#user-full-name-to-replace').textContent = userFullName;
        var modalForm = modal.querySelector('form');
        var formActionUrl = modalForm.getAttribute('action');
        modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', siaeSlug).replace('siae-user-id-to-replace', siaeUserId));
    });
});
