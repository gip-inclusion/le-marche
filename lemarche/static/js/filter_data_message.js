function filterData(data, filterText) {
    return data.filter(item => {
        const from = `${item.From.Name} || ${item.From.Address}`;
        const to = item.To[0].Address;
        const RawHtmlBody = item.RawHtmlBody;
        // filter fields
        return from.includes(filterText) || to.includes(filterText) || RawHtmlBody.includes(filterText);
    });
}

// Fonction pour générer les lignes du tableau HTML
function generateTableRows(filteredData) {
    const rows = filteredData.map(item => {
        const sendAt = new Date(item.SentAtDate).strftime('%d/%m/%Y %Hh%M');
        const from = `${item.From.Name} - ${item.From.Address}`;
        const attachementsCount = item.Attachments ? item.Attachments.length : 0;

        return `<tr>
                    <td>${sendAt}</td>
                    <td>${from}</td>
                    <td>${attachementsCount}</td>
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
    const headTable = `
        <tr>
            <th scope="col">Date d'envoi</th>
            <th scope="col">Expéditeur</th>
            <th scope="col">Nombre de PJ</th>
        </tr>
    `;
    const tableRows = headTable + generateTableRows(rawData);

    // insert rows
    dataTableBody.innerHTML = tableRows;
}

// Appeler la fonction init lorsque la page est chargée
document.addEventListener('DOMContentLoaded', init);
