document.addEventListener('alpine:init', function () {
    Alpine.data('activityItem', () => ({
        siaeActivityId: null,
        siaeActivityNameDisplay: null,

        initOptions(siaeActivityId, siaeActivityNameDisplay) {
            this.siaeActivityId = siaeActivityId;
            this.siaeActivityNameDisplay = siaeActivityNameDisplay;
        },
        remove() {
            // Update the modal's content
            // - siae activity name display
            // - edit the form action url
            // - open the modal
            let modalID = 'siae_activity_delete_modal';
            let modal = document.querySelector(`#${modalID}`);
            let modalForm = modal.querySelector('form');
            if (modal.querySelector('#siae-activity-name-display')) {
                modal.querySelector('#siae-activity-name-display').textContent = this.siaeActivityNameDisplay;
            }
            let formActionUrl = escapeHtml(modalForm.getAttribute('data-action'));
            modalForm.setAttribute('action', formActionUrl.replace('siae-activity-id-to-replace', this.siaeActivityId.replace(/\D/g, '')));

            const modalDialog = document.getElementById(modalID);
            dsfr(modalDialog).modal.disclose();
        }
    }));
});
