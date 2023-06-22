// need to setup "current-locations" div which contains the currents locations selected to manage the refresh page

const LOCATION_AUTOCOMPLETE_ID = 'id_locations';
const LOCATION_AUTOCOMPLETE_CONTAINER_SELECTOR = '#dir_form_locations';
const LOCATION_SELECTED_CONTAINER_SELECTOR = '#locations-selected';
const LOCATION_HIDDEN_INPUT_SELECTOR_PREFIX = 'hiddenLocation';
const LOCATION_CURRENT_ID = 'current-locations';
var KIND_MAPPING = {
  'REGION': 'région',
  'DEPARTMENT': 'département',
  'CITY': 'commune',
}
var API_ENDPOINT = '/api/perimeters/autocomplete/';

function removeInputOnClick() {
  let idRefInput = $(this).data('refinput');
  // remove the input
  $(`#${idRefInput}`).remove();
  $(this).remove();
}

function createHiddenInputLocation(resultId, resultName) {
  let locationAutocompleteContainer = document.querySelector(LOCATION_AUTOCOMPLETE_CONTAINER_SELECTOR);
  let locationsContainer = document.querySelector(LOCATION_SELECTED_CONTAINER_SELECTOR);
  let locationAutocompleteContainerInputName = locationAutocompleteContainer.dataset.inputName;

  let removeIcon = $('<i>', { class: "ri-close-line font-weight-bold mr-0", "aria-hidden": true });
  let resultIdString = `${LOCATION_HIDDEN_INPUT_SELECTOR_PREFIX}-${resultId}`;
  $('<input>', {
      type: 'hidden',
      id: resultIdString,
      name: locationAutocompleteContainerInputName,
      value: resultId
  }).appendTo(locationsContainer);
  let button = $('<button>', {
      type: 'button',
      class: "badge badge-base badge-pill badge-outline-primary mr-1 mb-1",
      title: `Retirer ${resultName}`,
      text: `${resultName}`,
      'data-refInput': resultIdString,
      click: removeInputOnClick
  });
  removeIcon.appendTo(button);
  button.appendTo(locationsContainer);
}
function cleanLocations() {
  var locationsContainer = document.querySelector(LOCATION_SELECTED_CONTAINER_SELECTOR);
  $(locationsContainer).empty();
}

/**
 * Accessible autocomplete for the location search form field
 */
function initLocationsAutoCompleteFields() {
  // let locationInput = document.getElementById(LOCATION_AUTOCOMPLETE_ID);  // hidden

  var locationAutocompleteContainer = document.querySelector(LOCATION_AUTOCOMPLETE_CONTAINER_SELECTOR);

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

  // https://github.com/alphagov/accessible-autocomplete/issues/210#issuecomment-549463974
  // function fetchSource(query, populateResults) {
  //   return fetch(`http://127.0.0.1:8000/api/perimeters/autocomplete/?q=${query}&results=10`)
  //     .then(r => r.json())
  //     .then(data => populateResults(data))
  // }
  async function fetchSource(query) {
    const res = await fetch(`${API_ENDPOINT}?q=${query}&results=10`);
    const data = await res.json();
    return data;  // data.results
  }

  function suggestion(result) {
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

  function inputValue(result) {
    return "";
  }

  function inputValueHiddenField(result) {
    // we want to avoid clicks outside that return 'undefined'
    if (result) {
      // if (typeof result === 'object') {
      //   locationInput.value = result.slug;
      // }
      // debugger
      createHiddenInputLocation(result.slug, result.name);  // result.id
      // // Edge case: if there is an initial value and it is selected again (!)  // commented out because the hidden input value is already set, no need to re-set it
      // if (typeof result === 'string') {
      //   locationInput.value = locationParamInitial;
      // }
    }
  }
  if (document.body.contains(locationAutocompleteContainer)) {
    accessibleAutocomplete({
      element: locationAutocompleteContainer,
      id: LOCATION_AUTOCOMPLETE_ID,
      name: '',  // url GET param name. empty to avoid having the default value appearing ('input-autocomplete')
      placeholder: 'Région, département, ville',  // 'Autour de (Arras, Bobigny, Strasbourg…)',
      minLength: 2,
      defaultValue: "",
      source: debounce(async (query, populateResults) => {
        const res = await fetchSource(query);
        populateResults(res);
        // we also reset the inputValueHiddenField because the location hasn't been chosen yet (will happen with onConfirm)
      }, 300),
      displayMenu: 'overlay',
      templates: {
        inputValue: inputValue,  // returns the string value to be inserted into the input
        suggestion: suggestion,  // used when rendering suggestions, and should return a string, which can contain HTML
      },
      autoselect: true,
      onConfirm: (confirmed) => {
        inputValueHiddenField(confirmed);
      },
      showNoOptionsFound: false,
      // Internationalization
      tNoResults: () => 'Aucun résultat',
      tStatusQueryTooShort: (minQueryLength) => `Tapez au moins ${minQueryLength} caractères pour avoir des résultats`,
      tStatusNoResults: () => 'Aucun résultat pour cette recherche',
      tStatusSelectedOption: (selectedOption, length, index) => `${selectedOption} ${index + 1} de ${length} est sélectionnée`,
      // tStatusResults:
      // tAssistiveHint:
    });
  }

  let currentLocationsElement = document.getElementById(LOCATION_CURRENT_ID);
  if (currentLocationsElement) {
    let currentLocations = JSON.parse(currentLocationsElement.textContent);
    if (currentLocations) {
      currentLocations.forEach(location => {
        createHiddenInputLocation(location['slug'], location['name']);  // parseInt(location['id'])
      });
    }
  }
}

document.addEventListener("DOMContentLoaded", function() {
  initLocationsAutoCompleteFields();
});

// document.body.addEventListener('htmx:afterSwap', function() {
//   initLocationsAutoCompleteFields();
// });
