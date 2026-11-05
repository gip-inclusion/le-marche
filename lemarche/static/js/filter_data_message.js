function filterData(data, filterText) {
    return data.filter(item => {
        const from = `${item.From.Name} || ${item.From.Address}`;
        const to = item.To[0].Address;
        const RawHtmlBody = item.RawHtmlBody;
        // filter fields
        return from.includes(filterText) || to.includes(filterText) || RawHtmlBody.includes(filterText);
    });
}

// Génère une ligne du tableau (valeurs insérées via textContent pour éviter toute injection HTML)
function createTableRow(cellValues, cellTag = 'td') {
    const row = document.createElement('tr');
    cellValues.forEach(value => {
        const cell = document.createElement(cellTag);
        if (cellTag === 'th') {
            cell.scope = 'col';
        }
        cell.textContent = value;
        row.appendChild(cell);
    });
    return row;
}

// Fonction pour générer les lignes du tableau HTML
function generateTableRows(filteredData) {
    return filteredData.map(item => {
        const sendAt = new Date(item.SentAtDate).strftime('%d/%m/%Y %Hh%M');
        const from = `${item.From.Name} - ${item.From.Address}`;
        const attachementsCount = item.Attachments ? item.Attachments.length : 0;

        return createTableRow([sendAt, from, attachementsCount]);
    });
}

function init() {
    const dataTableBody = document.getElementById('table_filter_data_message');
    const rawData = JSON.parse(dataTableBody.dataset.data);

    // Filter data
    // const filterInput = document.getElementsByName('id_data_filter');
    // const filterText = filterInput.value.trim().toLowerCase();
    // const filteredData = filterData(rawData, filterText);

    // generate rows
    const headRow = createTableRow(["Date d'envoi", "Expéditeur", "Nombre de PJ"], 'th');

    // insert rows
    dataTableBody.replaceChildren(headRow, ...generateTableRows(rawData));
}

// Appeler la fonction init lorsque la page est chargée
document.addEventListener('DOMContentLoaded', init);
