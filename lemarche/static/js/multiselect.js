function multiselect() {
    return {
        open: false,
        selected: [],
        selectedLabels: '',
        toggle() {
            this.open = !this.open;
        },
        updateSelection(event) {
            const label = event.target.getAttribute('x-value');
            if (event.target.checked) {
                this.selected.push(label);
            } else {
                this.selected = this.selected.filter(item => item !== label);
            }
            this.updateInput();
        },
        updateInput() {
            this.selectedLabels = this.selected.map(label => {
                if (label.length > 10) {
                    return label.substring(0, 10) + '...';
                }
                return label;
            }).join(', ');
        }
    };
}
