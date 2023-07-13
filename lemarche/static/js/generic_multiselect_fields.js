document.addEventListener('DOMContentLoaded', function () {
    /**
     * Multiselect dropdown for search form field
     */

    const MULTI_SELECT_FIELDS = [
        { "id": "id_kind", "placeholder": "Insertion, handicap", "more_designation": "types sélectionnés" },
        { "id": "id_legal_form", "placeholder": "Association, SARL", "more_designation": "formes sélectionnées" },
        { "id": "id_labels", "placeholder": "ESUS, RGE", "more_designation": "certifications sélectionnées" },
    ];

    for (let i = 0; i < MULTI_SELECT_FIELDS.length; i++) {

        const FORM_INPUT_ID = MULTI_SELECT_FIELDS[i]["id"];
        const FORM_MULTISELECT_ID = `${FORM_INPUT_ID}_multiselect`;
        const FORM_ELEMENT = document.querySelector(`#filter-search-form #${FORM_INPUT_ID}`);
        const FORM_PLACEHOLDER = MULTI_SELECT_FIELDS[i]["placeholder"];

        const buttonTextAndTitle = function (options, select) {
            if (options.length === 0) {
                return FORM_PLACEHOLDER;
            }
            else if (options.length > 2) {
                return `${options.length} ${MULTI_SELECT_FIELDS[i]["more_designation"]}`;
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
    }
});
