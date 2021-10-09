document.addEventListener("DOMContentLoaded", function() {

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
    console.log("fetchSource", query, data)
    return data.results;
}

  function inputValue(result) {
    return result && result.slug;
  }

  function suggestion(result) {
    const kind = perimeterKindMapping[result.kind];
    const nameWithKind = '<strong>' + result.name + '</strong>' + ' <small>(' + kind + ')</small>'
    return result && nameWithKind;
  }
  
  accessibleAutocomplete({
    element: document.querySelector('#dir_form_perimeter'),
    id: 'perimeter',
    name: 'perimeter',  // url GET param name
    placeholder: 'Autour de (Arras, Bobigny, Strasbourg…)',
    minLength: 2,
    // source: (query, populateResults) => fetchSource(query, populateResults),
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
    showNoOptionsFound: false,
    // Internationalization
    tNoResults: () => 'Aucun résultats',
  })

  // accessibleAutocomplete.enhanceSelectElement({
  //   selectElement: document.querySelector('#id_perimeter'),
  //   source: countries
  // })
});
