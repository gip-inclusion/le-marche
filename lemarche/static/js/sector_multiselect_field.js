document.addEventListener('DOMContentLoaded', function() {
    /**
     * Multiselect dropdown for the sector search form field
     */

    const sectorFormElement = document.querySelector('.use-multiselect #id_sectors');
    const sectorFormPlaceholder = 'Espaces verts, informatique, restauration…';

    const buttonTextAndTitle = function(options, select) {
        if (options.length === 0) {
            return sectorFormPlaceholder;
        }
        else if (options.length > 2) {
            return `${options.length} secteurs sélectionnés`;
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

    // only on pages with id_sectors
    if (document.body.contains(sectorFormElement)) {
        $('#id_sectors').multiselect({
            // height & width
            maxHeight: 400,
            buttonWidth: '100%',
            widthSynchronizationMode: 'always',
            // button
            buttonTextAlignment: 'left',
            buttonText: buttonTextAndTitle,
            buttonTitle: buttonTextAndTitle,
            // filter options
            enableFiltering: true,
            enableCaseInsensitiveFiltering: true,
            filterPlaceholder: sectorFormPlaceholder,
            // reset button
            includeResetOption: true,
            includeResetDivider: true,
            resetText: 'Réinitialiser la sélection',
            // enableResetButton: true,
            // resetButtonText: 'Réinitialiser',
            // ability to select all group's child options in 1 click
            enableClickableOptGroups: true,
            // other
            buttonContainer: '<div id="id_sectors_multiselect" class="btn-group" />',
            widthSynchronizationMode: 'ifPopupIsSmaller',
            // enableHTML: true,
            // nonSelectedText: `<span class="text-muted">${sectorFormPlaceholder}</span>`,
            templates: {
                resetButton: '<div class="multiselect-reset p-2"><button type="button" class="btn btn-sm btn-block btn-outline-primary"></button></div>',
                // buttonGroupReset: '<button type="button" class="multiselect-reset btn btn-outline-primary btn-block"></button>'
            }
        });

        // // fix bug where reset button didn't work on init
        // $('.multiselect-reset').on('click', function() {
        //     $('#id_sectors').multiselect('deselectAll');
        // });

        // hack to set the placeholder color to grey when there is no sector selected
        const multiselectSelectedText = document.querySelector('#id_sectors_multiselect .multiselect-selected-text');
        if (multiselectSelectedText.innerText === sectorFormPlaceholder) {
            multiselectSelectedText.classList.add('text-muted');
        }
        multiselectSelectedText.addEventListener('DOMSubtreeModified', function () {
            if (this.innerText === sectorFormPlaceholder) {
                this.classList.add('text-muted');
            } else {
                this.classList.remove('text-muted');
            }
        })
    }

});
