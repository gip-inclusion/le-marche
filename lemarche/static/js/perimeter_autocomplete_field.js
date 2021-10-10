document.addEventListener("DOMContentLoaded", function() {

  let perimeterNameInput = document.getElementById('id_perimeter_name');  // autocomplete
  let perimeterInput = document.getElementById('id_perimeter');  // hidden

  // check if there is an initial value for the autocomplete
  const urlParams = new URLSearchParams(window.location.search);
  const perimeterParam = urlParams.get('perimeter');
  const perimeterNameParam = urlParams.get('perimeter_name');
  const perimeterParamInitial = perimeterParam ? perimeterParam : '';
  const perimeterNameParamInitial = perimeterNameParam ? perimeterNameParam : '';

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
  //   return fetch(`http://127.0.0.1:8000/api/perimeters/?name=${query}&results=10`)
  //     .then(r => r.json())
  //     .then(data => populateResults(data))
  // }
  async function fetchSource(query) {
    const res = await fetch(`http://127.0.0.1:8000/api/perimeters/?name=${query}&results=10`);
    const data = await res.json();
    return data.results;
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
    // strip html from suggestion
    const resultValue = result ? suggestion(result).replace(/(<([^>]+)>)/gi, '') : '';
    return result && resultValue;
  }

  function inputValueHiddenField(result) {
    // we want to avoid clicks outside that return 'undefined'
    if (result) {
      if (typeof result === 'object') {
        perimeterInput.value = result.slug;
      }
      // // Edge case: if there is an initial value and it is selected again (!)  // commented out because the hidden input value is already set, no need to re-set it
      // if (typeof result === 'string') {
      //   perimeterInput.value = perimeterParamInitial;
      // }
    }
  }

  function resetInputValueHiddenField() {
    perimeterInput.value = '';
  }
  
  // https://github.com/alphagov/accessible-autocomplete
  accessibleAutocomplete({
    element: document.querySelector('#dir_form_perimeter_name'),
    id: 'perimeter_name',
    name: 'perimeter_name',  // url GET param name
    placeholder: 'Autour de (Arras, Bobigny, Strasbourg…)',
    minLength: 2,
    defaultValue: perimeterNameParamInitial,
    source: async (query, populateResults) => {  // TODO; use debounce ?
      const res = await fetchSource(query);
      populateResults(res);
      // we also reset the inputValueHiddenField because the perimeter hasn't been chosen yet (will happen with onConfirm)
      resetInputValueHiddenField();
    },
    displayMenu: 'overlay',
    templates: {
      inputValue: inputValue,  // returns the string value to be inserted into the input
      suggestion: suggestion,  // used when rendering suggestions, and should return a string, which can contain HTML
    },
    // autoselect: true,
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
  })

  if (perimeterNameInput) {
    perimeterNameInput.addEventListener('change', event => {
      console.log(event.target.value);
    })
  }
});
