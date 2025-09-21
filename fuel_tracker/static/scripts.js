document.getElementById('entryForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {};
    formData.forEach((value, key) => data[key] = value);
    
    const response = await fetch('/add', {
        method: 'POST',
        body: new URLSearchParams(data)
    });
    const json = await response.json();
    console.log(json);  // Process the JSON response
    location.reload();  // Refresh the page to update the entry list
});

document.getElementById('exportData').addEventListener('click', async function() {
    window.location.href = '/export';
});

document.getElementById('importData').addEventListener('click', async function() {
    const importFile = document.getElementById('importFile').files[0];
    if (importFile) {
        const formData = new FormData();
        formData.append('file', importFile);
        const response = await fetch('/import', {
            method: 'POST',
            body: formData
        });
        const json = await response.json();
        console.log(json);  // Process the JSON response
        location.reload();  // Refresh the page to update the entry list
    }
});

document.getElementById('restoreBackup').addEventListener('click', async function() {
    const response = await fetch('/restore', {
        method: 'POST'
    });
    const json = await response.json();
    console.log(json);  // Process the JSON response
    location.reload();  // Refresh the page to update the entry list
});

document.querySelectorAll('.delete-button').forEach(button => {
    button.addEventListener('click', async function() {
        const index = this.getAttribute('data-index');
        const response = await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ indices: [index] })
        });
        const json = await response.json();
        console.log(json);  // Process the JSON response
        location.reload();  // Refresh the page to update the entry list
    });
});

document.querySelectorAll('.edit-button').forEach(button => {
    button.addEventListener('click', function() {
        const index = this.getAttribute('data-index');
        const row = this.closest('tr');
        const date = row.children[0].innerText;
        const odometer = row.children[1].innerText;
        const fuel_price = row.children[2].innerText;
        const fuel = row.children[3].innerText;

        document.getElementById('date').value = date;
        document.getElementById('odometer').value = odometer;
        document.getElementById('fuel_price').value = fuel_price;
        document.getElementById('fuel').value = fuel;

        document.getElementById('entryForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = {};
            formData.forEach((value, key) => data[key] = value);

            const response = await fetch(`/edit/${index}`, {
                method: 'POST',
                body: new URLSearchParams(data)
            });
            const json = await response.json();
            console.log(json);  // Process the JSON response
            location.reload();  // Refresh the page to update the entry list
        }, { once: true });
    });
});
