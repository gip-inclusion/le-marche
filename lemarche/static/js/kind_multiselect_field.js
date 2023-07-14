document.addEventListener('DOMContentLoaded', function () {
    /**
     * Multiselect dropdown for the kind search form field
     */

    const FORM_INPUT_ID = "id_kind";
    const FORM_MULTISELECT_ID = `${FORM_INPUT_ID}_multiselect`;
    const FORM_ELEMENT = document.querySelector(`#filter-search-form #${FORM_INPUT_ID}`);
    const FORM_PLACEHOLDER = 'Insertion, handicap';

    const buttonTextAndTitle = function (options, select) {
        if (options.length === 0) {
            return FORM_PLACEHOLDER;
        }
        else if (options.length > 2) {
            return `${options.length} types sélectionnés`;
        }
        else {
            var labels = [];
            options.each(function () {
                if ($(this).attr('label') !== undefined) {
                    labels.push($(this).attr('label'));
                }
                else {
                    labels.push($(this).html());
                }
            });
            return labels.join(', ') + '';
        }
    }

    if (document.body.contains(FORM_ELEMENT)) {
        $(`#${FORM_INPUT_ID}`).multiselect({
            // height & width
            maxHeight: 400,
            buttonWidth: '100%',
            widthSynchronizationMode: 'always',
            // button
            buttonTextAlignment: 'left',
            buttonText: buttonTextAndTitle,
            buttonTitle: buttonTextAndTitle,
            // ability to select all group's child options in 1 click
            enableClickableOptGroups: true,
            // other
            buttonContainer: `<div id="${FORM_MULTISELECT_ID}" class="btn-group" />`,
            widthSynchronizationMode: 'ifPopupIsSmaller',
            // enableHTML: true,
            // nonSelectedText: `<span class="fake-placeholder">${FORM_PLACEHOLDER}</span>`,
        });

        // hack to set the placeholder color to grey when there is no item selected
        const multiselectSelectedText = document.querySelector(`#${FORM_MULTISELECT_ID} .multiselect-selected-text`);
        if (multiselectSelectedText.innerText === FORM_PLACEHOLDER) {
            multiselectSelectedText.classList.add('fake-placeholder');
        }
        document.addEventListener('DOMSubtreeModified', function () {
            const multiselectSelectedText = document.querySelector(`#${FORM_MULTISELECT_ID} .multiselect-selected-text`);
            if (multiselectSelectedText.innerText === FORM_PLACEHOLDER) {
                multiselectSelectedText.classList.add('fake-placeholder');
            } else {
                multiselectSelectedText.classList.remove('fake-placeholder');
            }
        })
    }

});
