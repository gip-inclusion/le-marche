// disable geo range custom distance if geo range is not CUSTOM
// for siae activity: hide or show entire form row (instead of just disabling)
document.addEventListener('DOMContentLoaded', function() {
    let geoRangeRadios = document.querySelectorAll('input[type=radio][name="geo_range"]');
    let geoRangeCustomDistanceInput = document.getElementById('id_geo_range_custom_distance');
    let geoRangeActivityRowInput = document.getElementById('geo_range_activity_row');

    // init
    geoRangeRadios.forEach(radio => {
        if (radio.checked && radio.value !== 'CUSTOM') {
            geoRangeCustomDistanceInput.disabled = true;
            geoRangeActivityRowInput.style.display = 'none';
        }
    });
    // on change
    geoRangeRadios.forEach(radio => radio.addEventListener('change', () => {
        if (radio.value !== 'CUSTOM') {
            geoRangeCustomDistanceInput.disabled = true;
            geoRangeActivityRowInput.style.display = 'none';
        } else {
            geoRangeCustomDistanceInput.disabled = false;
            geoRangeActivityRowInput.style.display = 'block';
        }
    }));
});
