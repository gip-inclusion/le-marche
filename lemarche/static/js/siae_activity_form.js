document.body.addEventListener('htmx:afterSettle', function() {
    let sectorGroupLabel = document.querySelector('#checkboxes-id_sectors label[class="form-check-label"]');
    console.log(sectorGroupLabel);
    if (sectorGroupLabel) {
        if (!sectorGroupLabel.hasAttribute('for')) {
            sectorGroupLabel.classList.add('hidden-label');
        } else {
            sectorGroupLabel.classList.remove('hidden-label'); 
        }
    }
});
