
let toggleRequiredInFieldset = (required, element) => {
    element.required = required;
    
    // Find the sibling label of the element
    let label = element.labels.length > 0 ? element.labels[0] : null;
    if (label) {
        // Check if the label already contains a "*" at the end
        let isAsteriskPresent = label.textContent.trim().endsWith("*");
        if (required && !isAsteriskPresent) {
            label.textContent += "*";
        } else if (!required && isAsteriskPresent) {
            label.textContent = label.textContent.trim().slice(0, -1);
        }
    }
}

let toggleFieldsetElement = (toggle, element, required = undefined) => {
    if (toggle) {
        element.classList.remove('fr-hidden');
    } else {
        element.classList.add('fr-hidden');
    }    
    let inputElements = element.querySelectorAll('input');
    if (inputElements.length > 0) {
        toggleRequiredInFieldset(required, inputElements[0]);
    } else {
        let selectElements = element.querySelectorAll('select');
        if (selectElements.length > 0) {
            toggleRequiredInFieldset(required, selectElements[0]);
        }
    }
}
