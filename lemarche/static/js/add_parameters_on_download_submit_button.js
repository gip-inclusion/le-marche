document.addEventListener("DOMContentLoaded", function() {
    $('#download_click_survey_modal').on('show.bs.modal', function (event) {
        let extraData = $(event.relatedTarget).data('extra');
        let submitButton = document.getElementById("button[type='submit']");
    });
});
