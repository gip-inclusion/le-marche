document.addEventListener('DOMContentLoaded', function() {
    let phoneFieldsetElement = document.getElementById('phoneFieldsetElement');
    let companyNameSiaeFormGroupDiv = document.getElementsByClassName('company-name-siae-form-group')[0];
    let infoStructuresFieldset = document.getElementById('infoStructuresFieldset');
    let buyerKindDetailFieldsetElement = document.getElementById('buyerKindDetailFieldsetElement');
    let partnerKindFieldsetElement = document.getElementById('partnerKindFieldsetElement');
    let companyNameFieldsetElement = document.getElementById('companyNameFieldsetElement');
    let positionFieldsetElement = document.getElementById('positionFieldsetElement');
    let sectorsFieldsetElement = document.getElementById('sectorsFieldsetElement');
    

    let kindRadios = document.querySelectorAll('input[type=radio][name="kind"]');
    kindRadios.forEach(radio => radio.addEventListener('change', () => {
        /* Phone field required for BUYER and SIAE */
        if (radio.value === 'BUYER' || radio.value === 'SIAE') {
            toggleFieldsetElement(true, element=phoneFieldsetElement, required=true);
        } else {
            toggleFieldsetElement(true, element=phoneFieldsetElement, required=false);
        }

        if (radio.value === 'SIAE') {
            companyNameSiaeFormGroupDiv.classList.remove('fr-hidden');
            toggleFieldsetElement(false, element=companyNameFieldsetElement, required=false);
        } else {
            companyNameSiaeFormGroupDiv.classList.add('fr-hidden');
            toggleFieldsetElement(true, element=companyNameFieldsetElement, required=true);
        }

        if (radio.value === 'BUYER') {
            toggleFieldsetElement(true, element=buyerKindDetailFieldsetElement, required=true);
            toggleFieldsetElement(true, element=positionFieldsetElement, required=true);
            toggleFieldsetElement(true, element=sectorsFieldsetElement, required=false);
        } else {
            toggleFieldsetElement(false, element=buyerKindDetailFieldsetElement, required=false);
            toggleFieldsetElement(false, element=positionFieldsetElement, required=false);
            toggleFieldsetElement(false, element=sectorsFieldsetElement, required=false);
        }

        if (radio.value === 'PARTNER') {
            toggleFieldsetElement(true, element=partnerKindFieldsetElement, required=true);
        } else {
            toggleFieldsetElement(false, element=partnerKindFieldsetElement, required=false);
        }

        if (radio.value === 'INDIVIDUAL') {
            toggleFieldsetElement(false, element=companyNameFieldsetElement, required=false);
            infoStructuresFieldset.classList.add('fr-hidden');
        } else {
            infoStructuresFieldset.classList.remove('fr-hidden');
        }
    }));
});