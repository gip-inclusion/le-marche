// https://www.joshwcomeau.com/snippets/javascript/debounce/
const debounce = (callback, wait) => {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      callback.apply(null, args);
    }, wait);
  };
}

async function fetchSource(query) {
  const res = await fetch(`/api/perimeters/autocomplete/?q=${query}&results=10`);
  const data = await res.json();
  return data;  // data.results
}

perimeterKindMapping = {
  'REGION': 'région',
  'DEPARTMENT': 'département',
  'CITY': 'commune',
}

class PerimeterAutoComplete {

    constructor(perimeter_container_name, perimeter_input_id) {
      this.perimeter_container_name= perimeter_container_name
      this.perimeter_input_id= perimeter_input_id
      this.perimeter_name_input_id= `${this.perimeter_input_id}_name`
      this.perimeterAutocompleteContainer = document.getElementById(perimeter_container_name);
      this.perimeterInput = document.getElementById(perimeter_input_id);  // hidden
      this.initial_value_name = this.perimeterAutocompleteContainer.dataset.inputValue;
      this.isInit = false;
    }

    init(){
      if(!this.isInit){
        this.isInit = true
        accessibleAutocomplete({
          element: this.perimeterAutocompleteContainer,
          id: this.perimeter_name_input_id,
          name: this.perimeter_name_input_id,  // url GET param name
          placeholder: 'Région, ville…',  // 'Autour de (Arras, Bobigny, Strasbourg…)', 'Région, département, ville'
          minLength: 2,
          defaultValue: this.initial_value_name,
          source:  this.getSource,
          displayMenu: 'overlay',
          templates: {
            inputValue: this.inputValue,  // returns the string value to be inserted into the input
            suggestion: this.inputValue,  // used when rendering suggestions, and should return a string, which can contain HTML
          },
          autoselect: true,
          onConfirm: (confirmed) => {
            this.inputValueHiddenField(confirmed);
          },
          showNoOptionsFound: false,
          // Internationalization
          tNoResults: this.tNoResults,
          tStatusQueryTooShort: this.tStatusQueryTooShort,
          tStatusNoResults: this.tStatusNoResults,
          tStatusSelectedOption: this.tStatusSelectedOption,
        });
        // after creation of input autocomplete, we set the div as attribute
        this.perimeterInputName = document.getElementById(this.perimeter_name_input_id);

      }
    }
    tNoResults = () => 'Aucun résultat'
    tStatusQueryTooShort = (minQueryLength) => `Tapez au moins ${minQueryLength} caractères pour avoir des résultats`
    tStatusNoResults = () => 'Aucun résultat pour cette recherche'
    tStatusSelectedOption = (selectedOption, length, index) => `${selectedOption} ${index + 1} de ${length} est sélectionnée`

    async getSource(query, populateResults) {
      const res = await fetchSource(query);
      populateResults(res);
    }

    inputValue(result) {
      // strip html from suggestion
      if(!result) {
        return result;
      }
      let resultName, resultKind = '';

      // build resultName & resultKind from the result object
      if (typeof result === 'object') {
        resultName = result.name;
        resultKind = (result.kind === 'CITY') ? result.department_code : perimeterKindMapping[result.kind];
      }

      // Edge case: if there is an initial value
      // reconstruct resultName & resultKind from the result string
      if (typeof result === 'string') {
        resultName = result.substring(0, result.lastIndexOf(' '));
        resultKind = result.includes('(') ? result.substring(result.lastIndexOf(' ') + 2, result.length - 1) : '';
      }

      let nameWithKind = '<strong>' + resultName + '</strong>';
      if (resultKind) {
        nameWithKind += ' <small>(' + resultKind + ')</small>';
      }
      return nameWithKind.replace(/(<([^>]+)>)/gi, '');
    }

    inputValueHiddenField(result) {
      // we want to avoid clicks outside that return 'undefined'
      if (result) {
        if (typeof result === 'object') {
          this.perimeterInput.value = result.id;
        }
      }
    }

    resetInputValueHiddenField() {
      this.perimeterInput.value = '';
    }


    cleanPerimeter() {
      this.perimeterInputName.value ='';
      this.perimeterInput.value ='';
    }

    disablePerimeter(disable_it=true) {
      if(disable_it){
        this.cleanPerimeter();
        this.perimeterInput.setAttribute('disabled', true);
        this.perimeterInputName.setAttribute('disabled', true);
      } else {
        this.perimeterInput.removeAttribute('disabled');
        this.perimeterInputName.removeAttribute('disabled');
      }
    }
}
