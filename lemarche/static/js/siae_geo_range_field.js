// disable geo range custom distance if geo range is not CUSTOM
document.addEventListener('DOMContentLoaded', function() {
    let geoRangeCustomDistanceInput = document.getElementById('id_geo_range_custom_distance');

    let geoRangeRadios = document.querySelectorAll('input[type=radio][name="geo_range"]');
    // init
    geoRangeRadios.forEach(radio => {
        if (radio.checked && radio.value !== 'CUSTOM') {
            geoRangeCustomDistanceInput.disabled = true;
        }
    });
    // on change
    geoRangeRadios.forEach(radio => radio.addEventListener('change', () => {
        if (radio.value !== 'CUSTOM') {
            geoRangeCustomDistanceInput.disabled = true;
        } else {
            geoRangeCustomDistanceInput.disabled = false;
        }
    }));
});
