document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('tender-send-confirmation-modal');
    const confirmBtn = document.getElementById('submit-button');
    const cancelBtn = document.getElementById('cancel-button');

    function openModal(recipient, title) {
        const messageElement = document.getElementById('tender-send-message');

        // Set an attribute 'name' depending on the recipient
        if (recipient === 'siaes') {
            messageElement.textContent = "Le besoin « " + title + " » sera envoyé aux structures.";
            confirmBtn.setAttribute('name', '_validate_send_to_siaes');
        } else if (recipient === 'partners') {
            messageElement.textContent = "Le besoin « " + title + " » sera envoyé aux partenaires.";
            confirmBtn.setAttribute('name', '_validate_send_to_commercial_partners');
        }
        modal.style.display = 'block';
    }

    // data-recipent attribute determines the recipient of the tender
    const buttons = document.querySelectorAll('input[data-recipient]');
    buttons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent instant form submission
            const recipient = button.getAttribute('data-recipient');
            const title = button.getAttribute('data-title');
            openModal(recipient, title);
        });
    });

    function closeModal() {
        modal.style.display = 'none';
    }

    // Two different ways to close the modal:
    // click on the cancel button
    cancelBtn.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent page from scrolling up
        closeModal();
    });    

    // click outside the modal
    window.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Action confirmation
    confirmBtn.addEventListener('click', function () {
        if (formToSubmit) {
            formToSubmit.submit();
        }
    });
});
