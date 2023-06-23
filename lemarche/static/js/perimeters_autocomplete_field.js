/**
 * 
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



