document.addEventListener("DOMContentLoaded", function() {

  const autocompletePerimeterInput = document.getElementById('id_perimeter_name');
  const hiddenPerimeterInput = document.getElementById('id_perimeter');

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
      resultKind = result.substring(result.lastIndexOf(' ') + 2, result.length - 1);
    }

    const nameWithKind = '<strong>' + resultName + '</strong>' + ' <small>(' + resultKind + ')</small>'
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
        hiddenPerimeterInput.value = result.slug;
      }

      // // Edge case: if there is an initial value and it is selected again (!)  // commented out because the hidden input value is already set, no need to re-set it
      // if (typeof result === 'string') {
      //   hiddenPerimeterInput.value = perimeterParamInitial;
      // }
    }
  }
  
  // https://github.com/alphagov/accessible-autocomplete
  accessibleAutocomplete({
    element: document.querySelector('#dir_form_perimeter_name'),
    id: 'perimeter_name',
    name: 'perimeter_name',  // url GET param name
    placeholder: 'Autour de (Arras, Bobigny, Strasbourg…)',
    minLength: 2,
    defaultValue: perimeterNameParamInitial,
    source: async (query, populateResults) => {
      const res = await fetchSource(query);
      populateResults(res);
    },
    // source: debounce(async (query, populateResults) => {
    //   const res = await fetchSource(query);
    //   populateResults(res);
    // }, 150),
    displayMenu: 'overlay',
    templates: {
      inputValue: inputValue,  // returns the string value to be inserted into the input
      suggestion: suggestion,  // used when rendering suggestions, and should return a string, which can contain HTML
    },
    onConfirm: (confirmed) => {
      inputValueHiddenField(confirmed);
    },
    showNoOptionsFound: false,
    // Internationalization
    tNoResults: () => 'Aucun résultat',
  })
});
