document.addEventListener('alpine:init', function () {
    Alpine.data('siaeUserModals', () => ({
        siaeSlug: null,
        id: null,
        fullName: null,

        initOptions(siaeSlug, fullName, id) {
            this.siaeSlug = siaeSlug;
            this.fullName = fullName;
            this.id = id;
        },
        openModal(modalID, replaceIdSelector) {
            // Update the modal's content
            // - edit the form action url
            // - open the modal
            let modal = document.querySelector(`#${modalID}`);
            let modalForm = modal.querySelector('form');
            let formActionUrl = modalForm.getAttribute('data-action');
            modal.querySelector('#full-name-to-replace').textContent = this.fullName;
            modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', this.siaeSlug).replace(replaceIdSelector, this.id));
            dsfr(modal).modal.disclose();
        },
        confirmUserRequest() {
            this.openModal('siae_user_request_confirm_modal', 'siae-user-request-id-to-replace');
        },
        cancelUserRequest() {
            this.openModal('siae_user_request_cancel_modal', 'siae-user-request-id-to-replace');
        },
        deleteUser() {
            this.openModal('siae_user_delete_modal', 'siae-user-id-to-replace');
        }
    }));
});
