function filterData(data, filterText) {
    return data.filter(item => {
        const from = `${item.items[0].From.Name} || ${item.items[0].From.Address}`;
        const to = item.items[0].To[0].Address;
        const RawHtmlBody = item.items[0].RawHtmlBody;
        // filter fields
        return from.includes(filterText) || to.includes(filterText) || RawHtmlBody.includes(filterText);
    });
}

// Fonction pour générer les lignes du tableau HTML
function generateTableRows(filteredData) {
    const rows = filteredData.map(item => {
        const sendAt = new Date(item.items[0].SentAtDate).strftime('%d/%m/%Y %Hh%M');
        const from = `${item.items[0].From.Name} - ${item.items[0].From.Address}`;
        const RawHtmlBody = item.items[0].RawHtmlBody ? item.items[0].RawHtmlBody : item.items[0].RawTextBody;

        return `<tr>
                    <td>${sendAt}</td>
                    <td>${from}</td>
                    <td>${RawHtmlBody}</td>
                </tr>`;
    });

    return rows.join('');
}

function init() {
    const dataTableBody = document.getElementById('table_filter_data_message');
    const rawData = JSON.parse(dataTableBody.dataset.data);

    // Filter data
    // const filterInput = document.getElementsByName('id_data_filter');
    // const filterText = filterInput.value.trim().toLowerCase();
    // const filteredData = filterData(rawData, filterText);

    // generate rows
    const tableRows = generateTableRows(rawData);

    // insert rows
    dataTableBody.innerHTML = tableRows;
}

// Appeler la fonction init lorsque la page est chargée
document.addEventListener('DOMContentLoaded', init);
