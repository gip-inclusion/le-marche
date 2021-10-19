// https://github.com/betagouv/itou/blob/master/itou/static/js/utils.js

$(document).ready(() => {
    // prevent default on click
    $(".js-prevent-default").on("click", (event) => {
        event.preventDefault();
    });

    // element will be hidden if JS is disabled
    $(".js-display-if-javascript-enabled").css("display", "block");
});
