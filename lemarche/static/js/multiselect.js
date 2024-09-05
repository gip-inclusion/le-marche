document.addEventListener('alpine:init', () => {
    Alpine.store('dropdown', {
        active: null,

        open(dropdown) {
            if (this.active && this.active !== dropdown) {
                this.active.closeDropdown();
            }
            this.active = dropdown;
        },

        close() {
            if (this.active) {
                this.active.closeDropdown();
                this.active = null;
            }
        }
    });

    // Composant Alpine.js pour le multi-sélecteur
    Alpine.data('multiselect', (id) => ({
        open: false,
        selected: [],
        selectedValues: [],
        searchQuery: '',
        groups: [],
        options: [],
        filteredGroups: [],
        filteredOptions: [],
        name: id,

        initOptions(groupsJson, optionsJson) {
            if (groupsJson) {
                this.groups = JSON.parse(groupsJson);
                this.filteredGroups = this.groups;
            }
            if (optionsJson) {
                this.options = JSON.parse(optionsJson);
                this.filteredOptions = this.options;
            }

            this.initSelectedValuesFromURL();  // Initialiser les tags à partir des valeurs de l'URL
        },

        initSelectedValuesFromURL() {
            const urlParams = new URLSearchParams(window.location.search);
            const values = urlParams.getAll(this.name);

            values.forEach(value => {
                const option = this.findOptionByValue(value);
                if (option) {
                    this.selectedValues.push(value);
                    this.selected.push(option.label);
                }
            });

            // this.updateInput();
        },

        findOptionByValue(value) {
            let foundOption = null;

            if (this.groups.length > 0) {
                this.groups.forEach(group => {
                    group.options.forEach(option => {
                        if (option.value === value) {
                            foundOption = option;
                        }
                    });
                });
            }

            if (!foundOption) {
                this.options.forEach(option => {
                    if (option.value === value) {
                        foundOption = option;
                    }
                });
            }

            return foundOption;
        },

        openDropdown() {
            this.open = true;
            Alpine.store('dropdown').open(this);  // Gérer l'état global du dropdown actif
        },

        closeDropdown() {
            this.open = false;
        },

        filterOptions() {
            if (!this.open) {
                this.open = true;
            }
            const searchQueryLower = this.searchQuery.toLowerCase();
            if (this.groups.length > 0) {
                this.filteredGroups = this.groups.map(group => ({
                    ...group,
                    options: group.options.filter(option =>
                        option.label.toLowerCase().includes(searchQueryLower)
                    )
                })).filter(group => group.options.length > 0);
            } else {
                this.filteredOptions = this.options.filter(option =>
                    option.label.toLowerCase().includes(searchQueryLower)
                );
            }
        },

        updateSelection(label, value) {
            const valueIndex = this.selectedValues.indexOf(value);
            if (valueIndex === -1) {
                this.selectedValues.push(value);
                this.selected.push(label);
            } else {
                this.selectedValues.splice(valueIndex, 1);
                this.selected = this.selected.filter(item => item !== label);
            }
            this.updateInput();
        },

        removeSelection(index) {
            const value = this.selectedValues[index];
            this.selectedValues.splice(index, 1);
            this.selected.splice(index, 1);
            this.updateInput();
        },

        updateInput() {
            this.searchQuery = '';
            this.filterOptions();
        }
    }));
});
