// https://github.com/betagouv/itou/blob/master/itou/static/js/utils.js

$(document).ready(() => {
    // prevent default on click
    $('.js-prevent-default').on('click', (event) => {
        event.preventDefault();
    });

    // element will be hidden if JS is disabled
    $('.js-display-if-javascript-enabled').css('display', 'block');

    // only way found to select checkbox group titles
    $('#id_sectors').children('.form-check.checkbox-title').contents().filter(function() {
        return this.nodeType == 3;
    }).wrap('<span class="group-title"></span>');
});
