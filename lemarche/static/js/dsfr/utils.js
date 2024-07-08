
let toggleRequiredInFieldset = (toggle, element) => {
    element.required = toggle;
    // FIXME: find required class or add *
    /*elementToToggle = element.parentNode.classList.contains("form-group") ? element.parentNode : element.parentNode.parentNode;
    if (toggle) {
        elementToToggle.classList.add('form-group-required');
    } else {
        elementToToggle.classList.remove('form-group-required');
    }*/
};

let toggleFieldsetElement = (toggle, element, required = undefined) => {
    if (toggle) {
        element.classList.remove('fr-hidden');
    } else {
        element.classList.add('fr-hidden');
    }
    
    let inputElements = element.querySelectorAll('input');
    if (inputElements.length > 0) {
        toggleRequiredInFieldset(toggle, inputElements[0]);
    } else {
        let selectElements = element.querySelectorAll('select');
        if (selectElements.length > 0) {
            toggleRequiredInFieldset(toggle, selectElements[0]);
        }
    }
}
