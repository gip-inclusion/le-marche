const MULTI_SELECT_TO_CLEAR = ["id_kind", "id_sectors", "id_presta_type", "id_territory", "id_networks"];

function clearFormFields(form) {
    // Parcourir tous les éléments du formulaire
    Array.from(form.elements).forEach(element => {
        const elementType = element.type.toLowerCase();
        // Effacer la valeur des champs en fonction du type
        switch (elementType) {
            case 'text':
            case 'password':
            case 'textarea':
            case 'hidden':
                element.value = '';
                break;

            case 'radio':
            case 'checkbox':
                element.checked = false;
                break;

            case 'select':
                debugger
                break;

            case 'select-one':
            case 'select-multiple':
                element.selectedIndex = -1;
                break;

            default:
                break;
        }
    });
}
function resetForm() {
    // Effacer les champs du formulaire
    const form = document.getElementById("filter-search-form");

    // Supprimer les boutons de la div #perimeters-selected
    const perimetersSelectedDiv = document.getElementById("perimeters-selected");
    while (perimetersSelectedDiv.firstChild) {
        perimetersSelectedDiv.firstChild.remove();
    }

    // Supprimer les boutons de la div #locations-selected
    const locationsSelectedDiv = document.getElementById("locations-selected");
    while (locationsSelectedDiv.firstChild) {
        locationsSelectedDiv.firstChild.remove();
    }

    // Réinitialiser les plugins jQuery multiselect
    clearFormFields(form);
    for (let i = 0; i < MULTI_SELECT_TO_CLEAR.length; i++) {
        let multiselect_component = $(`#${MULTI_SELECT_TO_CLEAR[i]}`);
        multiselect_component.multiselect("deselectAll", false)
        multiselect_component.multiselect("refresh");
    }
}

function showSearchFilterForm(searchFilterTab, searchFilterContent) {
    searchFilterTab.classList.add("active");
    searchFilterTab.setAttribute("aria-selected", "true");
    searchFilterContent.classList.add("show", "active");
}
function hideSearchFilterForm(searchFilterTab, searchFilterContent) {
    searchFilterTab.classList.remove("active");
    searchFilterTab.setAttribute("aria-selected", "false");
    searchFilterContent.classList.remove("show", "active");
}
function showSearchTextForm(searchTextTab, searchTextContent) {
    searchTextTab.classList.add("active");
    searchTextTab.setAttribute("aria-selected", "true");
    searchTextContent.classList.add("show", "active");
}
