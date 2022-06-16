document.addEventListener('DOMContentLoaded', function() {
    /**
     * Multiselect dropdown for the territory search form field
     */

    const territoryFormElement = document.querySelector('#search-form #id_territory');
    const territoryFormPlaceholder = 'QPV, ZRR';

    const buttonTextAndTitle = function(options, select) {
        if (options.length === 0) {
            return territoryFormPlaceholder;
        }
        else if (options.length > 2) {
            return `${options.length} territoires sélectionnés`;
        }
        else {
            var labels = [];
            options.each(function() {
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

    // only on pages with id_territory
    if (document.body.contains(territoryFormElement)) {
        $('#id_territory').multiselect({
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
            buttonContainer: '<div id="id_territory_multiselect" class="btn-group" />',
            widthSynchronizationMode: 'ifPopupIsSmaller',
            // enableHTML: true,
            // nonSelectedText: `<span class="fake-placeholder">${territoryFormPlaceholder}</span>`,
        });

        // hack to set the placeholder color to grey when there is no territory selected
        const multiselectSelectedText = document.querySelector('#id_territory_multiselect .multiselect-selected-text');
        if (multiselectSelectedText.innerText === territoryFormPlaceholder) {
            multiselectSelectedText.classList.add('fake-placeholder');
        }
        multiselectSelectedText.addEventListener('DOMSubtreeModified', function () {
            if (this.innerText === territoryFormPlaceholder) {
                this.classList.add('fake-placeholder');
            } else {
                this.classList.remove('fake-placeholder');
            }
        })
    }

});
