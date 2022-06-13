const perimeterAutocompleteContainer = document.querySelector('#dir_form_perimeter_name');
const perimetersContainer = document.querySelector('#perimeters-selected');

document.addEventListener("DOMContentLoaded", function() {
   /**
   * Accessible autocomplete for the perimeter search form field
   */



  // let perimeterInput = document.getElementById('id_perimeters');  // hidden

  const perimeterKindMapping = {
    'REGION': 'région',
    'DEPARTMENT': 'département',
    'CITY': 'commune',
  }

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
    const res = await fetch(`/api/perimeters/autocomplete/?q=${query}&results=10`);
    const data = await res.json();
    return data;  // data.results
  }

  function suggestion(result) {
    // display suggestions as `name (kind)`
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
    return result && nameWithKind;
  }

  function inputValue(result) {
    return "";
  }

  function removeInputOnClick() {
    let idRefInput = $(this).data('refinput');
    // remove the input
    $(`#${idRefInput}`).remove();
    $(this).remove();
  }


  function createHiddenInputPerimeter(result) {
    let removeIcon = $('<i>', { class: "ri-close-line ml-2", "aria-hidden": true });
    let idResult = `hiddenPermeter-${result.id}`;
    $('<input>', {
        type: 'hidden',
        id: idResult,
        name: 'general-perimeters',
        value: result.id
    }).appendTo(perimetersContainer);
    let button = $('<button>', {
        type: 'button',
        class: "btn btn-sm btn-outline-primary btn-warning mr-2",
        title: `Retirer ${result.name} du besoin`,
        text: `${result.name}`,
        'data-refInput': idResult,
        click: removeInputOnClick
    });
    removeIcon.appendTo(button);
    button.appendTo(perimetersContainer);
  }

  function inputValueHiddenField(result) {
    // we want to avoid clicks outside that return 'undefined'
    if (result) {
      // if (typeof result === 'object') {
      //   perimeterInput.value = result.slug;
      // }
      // debugger
      createHiddenInputPerimeter(result);
      // // Edge case: if there is an initial value and it is selected again (!)  // commented out because the hidden input value is already set, no need to re-set it
      // if (typeof result === 'string') {
      //   perimeterInput.value = perimeterParamInitial;
      // }
    }
  }


  if (document.body.contains(perimeterAutocompleteContainer)) {
    accessibleAutocomplete({
      element: perimeterAutocompleteContainer,
      id: 'perimeter_name',
      name: 'perimeter_name',  // url GET param name
      placeholder: 'Région, département, ville',  // 'Autour de (Arras, Bobigny, Strasbourg…)',
      minLength: 2,
      defaultValue: "",
      source: debounce(async (query, populateResults) => {
        const res = await fetchSource(query);
        populateResults(res);
        // we also reset the inputValueHiddenField because the perimeter hasn't been chosen yet (will happen with onConfirm)
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

});

function cleanPerimeters() {
  $(perimetersContainer).empty();
}