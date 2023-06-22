/**
 * Accessible autocomplete for the perimeter search form field
 * 
 * need to setup "current-perimeters" div which contains the currents perimeters selected to manage the refresh page
 */
var KIND_MAPPING = {
  'REGION': 'région',
  'DEPARTMENT': 'département',
  'CITY': 'commune',
}
var API_ENDPOINT = '/api/perimeters/autocomplete/';

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
  const res = await fetch(`${API_ENDPOINT}?q=${query}&results=10`);
  const data = await res.json();
  return data;  // data.results
}


class PerimetersAutoComplete {
  constructor(
    perimeter_autocomplete_id='id_perimeters',
    perimeter_autocomplete_container_selector='#dir_form_perimeters',
    perimeter_selected_container_selector='#perimeters-selected',
    perimeter_hidden_input_selector_prefix='hiddenPerimeter',
    perimeter_current_id='current-perimeters') {
    this.perimeter_autocomplete_id = perimeter_autocomplete_id;
    this.perimeter_autocomplete_container_selector = perimeter_autocomplete_container_selector;
    this.perimeter_autocomplete_container = document.querySelector(this.perimeter_autocomplete_container_selector);
    this.perimeter_autocomplete_container_input_name = this.perimeter_autocomplete_container.dataset.inputName;
    this.perimeter_selected_container_selector = perimeter_selected_container_selector;
    this.perimeter_selected_container = document.querySelector(perimeter_selected_container_selector);
    this.perimeter_hidden_input_selector_prefix = perimeter_hidden_input_selector_prefix;
    this.perimeter_current_id = perimeter_current_id;
    this.perimeter_current_container = document.getElementById(perimeter_current_id);
    this.isInit = false;
  }

  init() {
    if(!this.isInit) {
      this.isInit = true;

      accessibleAutocomplete({
        element: this.perimeter_autocomplete_container,
        id: this.perimeter_autocomplete_id,
        name: '',  // url GET param name. empty to avoid having the default value appearing ('input-autocomplete')
        placeholder: 'Région, département, ville',  // 'Autour de (Arras, Bobigny, Strasbourg…)',
        minLength: 2,
        defaultValue: "",
        source: debounce(this.getSource, 300),
        displayMenu: 'overlay',
        templates: {
          inputValue: this.inputValue,  // returns the string value to be inserted into the input
          suggestion: this.suggestion,  // used when rendering suggestions, and should return a string, which can contain HTML
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
        // tStatusResults:
        // tAssistiveHint:
      });

      if (this.perimeter_current_container) {
        let currentPerimeters = JSON.parse(this.perimeter_current_container.textContent);
        if (currentPerimeters) {
          currentPerimeters.forEach(perimeter => {
            this.createHiddenInputPerimeter(perimeter['slug'], perimeter['name']);  // parseInt(perimeter['id'])
          });
        }
      }
    }
  }

  tNoResults = () => 'Aucun résultat';
  tStatusQueryTooShort = (minQueryLength) => `Tapez au moins ${minQueryLength} caractères pour avoir des résultats`;
  tStatusNoResults = () => 'Aucun résultat pour cette recherche';
  tStatusSelectedOption = (selectedOption, length, index) => `${selectedOption} ${index + 1} de ${length} est sélectionnée`;

  async getSource(query, populateResults) {
    const res = await fetchSource(query);
    populateResults(res);
  }

  inputValue(result) {
    return "";
  }
  
  inputValueHiddenField(result) {
    // we want to avoid clicks outside that return 'undefined'
    if (result) {
      // if (typeof result === 'object') {
      //   perimeterInput.value = result.slug;
      // }
      // debugger
      this.createHiddenInputPerimeter(result.slug, result.name);  // result.id
      // // Edge case: if there is an initial value and it is selected again (!)  // commented out because the hidden input value is already set, no need to re-set it
      // if (typeof result === 'string') {
      //   perimeterInput.value = perimeterParamInitial;
      // }
    }
  }

  suggestion(result) {
    // display suggestions as `name (kind)`
    let resultName, resultKind = '';
  
    // build resultName & resultKind from the result object
    if (typeof result === 'object') {
      resultName = result.name;
      resultKind = (result.kind === 'CITY') ? result.department_code : KIND_MAPPING[result.kind];
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
    return result && nameWithKind;
  }

  removeInputOnClick() {
    let idRefInput = $(this).data('refinput');
    // remove the input
    $(`#${idRefInput}`).remove();
    $(this).remove();
  }
  
  createHiddenInputPerimeter(resultId, resultName) {
    let removeIcon = $('<i>', { class: "ri-close-line font-weight-bold mr-0", "aria-hidden": true });
    let resultIdString = `${this.perimeter_hidden_input_selector_prefix}-${resultId}`;
    $('<input>', {
        type: 'hidden',
        id: resultIdString,
        name: this.perimeter_autocomplete_container_input_name,
        value: resultId
    }).appendTo(this.perimeter_selected_container);
    let button = $('<button>', {
        type: 'button',
        class: "badge badge-base badge-pill badge-outline-primary mr-1 mb-1",
        title: `Retirer ${resultName}`,
        text: `${resultName}`,
        'data-refInput': resultIdString,
        click: this.removeInputOnClick
    });
    removeIcon.appendTo(button);
    button.appendTo(this.perimeter_selected_container);
  }

  cleanPerimeters() {
    $(this.perimeter_selected_container).empty();
  }
}
