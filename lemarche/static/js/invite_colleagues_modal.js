(function () {
    // Check if modal should be displayed (once every 6 months)
    const STORAGE_KEY = 'inviteColleaguesModalLastShown';
    const SIX_MONTHS_IN_MS = 6 * 30 * 24 * 60 * 60 * 1000; // Approximation: 6 months

    const lastShown = localStorage.getItem(STORAGE_KEY);
    const now = new Date().getTime();

    // Function to save the timestamp
    function saveModalShowTimestamp() {
        localStorage.setItem(STORAGE_KEY, new Date().getTime().toString());
    }

    // Show modal if never shown before or if 6 months have passed
    if (!lastShown || (now - parseInt(lastShown)) >= SIX_MONTHS_IN_MS) {
        // Wait for DSFR to be initialized
        window.addEventListener('load', function () {
            // Wait a bit for DSFR to be fully initialized
            setTimeout(() => {
                const modalDialog = document.getElementById('invite-colleagues-modal');
                if (modalDialog) {
                    dsfr(modalDialog).modal.disclose();
                    saveModalShowTimestamp();
                }
            }, 500);
        });
    }
})();
