const placeholder = 'Espaces verts, informatique, restauration…';

const buttonTextAndTitle = function(options, select) {
    if (options.length === 0) {
        return placeholder;
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

document.addEventListener('DOMContentLoaded', function() {
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
        filterPlaceholder: placeholder,
        // reset button
        includeResetOption: true,
        includeResetDivider: true,
        resetText: 'Réinitialiser',
        // enableResetButton: true,
        // resetButtonText: 'Réinitialiser',
        // ability to select all group's child options in 1 click
        enableClickableOptGroups: true,
        // other
        // enableHTML: true,
        // nonSelectedText: `<span class="text-muted">${placeholder}</span>`,
        templates: {
            resetButton: '<div class="multiselect-reset text-center p-2"><button type="button" class="btn btn-sm btn-block btn-outline-primary"></button></div>',
            // buttonGroupReset: '<button type="button" class="multiselect-reset btn btn-outline-primary btn-block"></button>'
        }
    });

    // // fix bug where reset button didn't work on init
    // $('.multiselect-reset').on('click', function() {
    //     $('#id_sectors').multiselect('deselectAll');
    // });

    // hack to set the placeholder color to grey when there is no sector selected
    if (document.querySelector('.multiselect-selected-text').innerText === placeholder) {
        document.querySelector('.multiselect-selected-text').classList.add('text-muted');
    }
    document.querySelector('.multiselect-selected-text').addEventListener('DOMSubtreeModified', function () {
        if (this.innerText === placeholder) {
            this.classList.add('text-muted');
        } else {
            this.classList.remove('text-muted');
        }
    })
});
