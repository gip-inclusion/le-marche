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
        filterPlaceholder: placeholder,
        // reset button
        enableResetButton: true,
        resetButtonText: 'Réinitialiser',
        // ability to select all group's child options in 1 click
        enableClickableOptGroups: true,
        // other
        // enableHTML: true,
        // nonSelectedText: `<span class="text-muted">${placeholder}</span>`,
    });

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
