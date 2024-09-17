document.addEventListener('alpine:init', function() {
    Alpine.data('favoriteItem', () => ({
        siaeSlug: null,
        siaeNameDisplay: null,
        
        initOptions(siaeSlug, siaeNameDisplay) {
            this.siaeSlug = siaeSlug;
            this.siaeNameDisplay = siaeNameDisplay;
        },
        add() {
            // Update the modal's content
            // - edit the form action url
            // - open the modal
            let modalID = 'favorite_item_add_modal';
            let modalForms = document.querySelector(`#${modalID}`).querySelectorAll('form');
            modalForms.forEach(form => {
                let formActionUrl = form.getAttribute('data-action');
                form.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', this.siaeSlug));
            });
            const modalDialog = document.getElementById(modalID);
            dsfr(modalDialog).modal.disclose();
        },
        remove() {
            // Update the modal's content
            // - siae name display
            // - edit the form action url
            // - open the modal
            let modalID = 'favorite_item_remove_modal';
            let modal = document.querySelector(`#${modalID}`);
            let modalForm = modal.querySelector('form');
            if (modal.querySelector('#siae-name-display')) {
                modal.querySelector('#siae-name-display').textContent = this.siaeNameDisplay;
            }
            let formActionUrl = modalForm.getAttribute('data-action');
            modalForm.setAttribute('action', formActionUrl.replace('siae-slug-to-replace', this.siaeSlug));

            const modalDialog = document.getElementById(modalID);
            dsfr(modalDialog).modal.disclose();
        }
    }));
});
