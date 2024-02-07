/**
 * Accessible autocomplete for the city search form field
 * https://alphagov.github.io/accessible-autocomplete/examples/
 *
 * CityAutocomplete:
 * - single city
 */
var API_ENDPOINT = '/api/cities/autocomplete/';

async function fetchSource(query) {
  const res = await fetch(`${API_ENDPOINT}?q=${query}&results=10`);
  const data = await res.json();
  return data;  // data.results
}

class CityAutocomplete {
  constructor(city_container_name, city_input_id) {
    this.city_container_name= city_container_name;
    this.city_input_id= city_input_id;
    this.city_name_input_id= `${this.city_input_id}_name`;
    this.cityAutocompleteContainer = document.getElementById(city_container_name);
    this.cityInput = document.getElementById(city_input_id);  // hidden
    this.initial_value_name = this.cityAutocompleteContainer.dataset.inputValue;
    this.isInit = false;
  }

  init() {
    if(!this.isInit) {
      this.isInit = true;
      accessibleAutocomplete({
        element: this.cityAutocompleteContainer,
        id: this.city_name_input_id,
        name: this.city_name_input_id,  // url GET param name
        placeholder: 'Ville',
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
      this.cityInputName = document.getElementById(this.city_name_input_id);
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
      resultKind = result.department_code;
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
        this.cityInput.value = result.slug;
      }
    }
  }

  resetInputValueHiddenField() {
    this.cityInput.value = '';
  }

  cleanCity() {
    this.cityInputName.value ='';
    this.cityInput.value ='';
  }

}
