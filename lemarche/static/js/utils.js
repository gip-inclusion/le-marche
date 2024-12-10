// https://github.com/betagouv/itou/blob/master/itou/static/js/utils.js

const rot13 = str => str.replace(/[a-z]/gi, letter => String.fromCharCode(letter.charCodeAt(0) + (letter.toLowerCase() <= 'm' ? 13 : -13)));

window.addEventListener('DOMContentLoaded', function () {
    // prevent default on click
    $('.js-prevent-default').on('click', (event) => {
        event.preventDefault();
    });

    // element will be hidden if JS is disabled
    $('.js-display-if-javascript-enabled').css('display', 'block');

    // only way found to select checkbox group titles
    $('#id_sectors').children('.form-check.checkbox-title').contents().filter(function () {
        return this.nodeType == 3;
    }).wrap('<span class="group-title"></span>');

    $('.btn_mail_encrypt').on('click', function (e) {
        location.href = "mailto:?" + rot13(this.dataset['nextUrl']);
    });

    initSuperBadges();

    // some elements have their url in data-url attribute
    $(document).on("click", ".with-data-url", function (e) {
        window.location.href = $(this).data("url");
    });
});

let toggleRequiredClasses = (toggle, element) => {
    element.required = required;
    elementToToggle = element.parentNode.classList.contains("form-group") ? element.parentNode : element.parentNode.parentNode;
    if (required) {
        elementToToggle.classList.add('form-group-required');
    } else {
        elementToToggle.classList.remove('form-group-required');
    }
};

let toggleInputElement = (toggle, element, required = undefined) => {
    // function usefull to find element form-group of bootstrap forms
    elementToToggle = element.parentNode.classList.contains("form-group") ? element.parentNode : element.parentNode.parentNode;
    if (toggle) {
        elementToToggle.classList.remove('d-none');
    } else {
        elementToToggle.classList.add('d-none');
    }
    if (required != undefined) {
        toggleRequiredClasses(required, element);
    }
}

const initSuperBadges = () => {
    $('.super-badge-badge').each(function (element) {
        $(this).tooltip(
            {
                html: true,
                placement: "bottom",
                title: $('#tooltip-super-badge').html()
            });
    });

    document.querySelectorAll('.siae-card[data-url]').forEach(function (card) {
        card.addEventListener('click', function (event) {
            if (event.target.className == 'ri-star-line ri-xl') {
                // manage case of favorites
                event.preventDefault();
            }
            else if (this.dataset.url) window.open(this.dataset.url, '_blank');

        });
    });
    $('#siaes_tabs .nav-item').on('click', function (event) {
        event.preventDefault()
        let tabContent = this.parentElement.parentElement.querySelector(".tab-content");
        let childLink = this.children[0];

        if (childLink.classList.contains("nav-link-external")) { //edge case for external links
            window.location = childLink.href;
        } else {
            let hasSuperBadgeTab = childLink.classList.contains("super-badge-tab");

            if (hasSuperBadgeTab) {
                tabContent.classList.add("super-badge-tab");
            } else {
                tabContent.classList.remove("super-badge-tab");
            }
        }
    })
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}