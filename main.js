function loadGrievances() {
    fetch('/get_grievances')
    .then(response => response.json())
    .then(data => {
        let grievanceTableBody = document.querySelector('#grievanceTable tbody');
        grievanceTableBody.innerHTML = '';  // Clear existing rows
        data.grievances.forEach(grievance => {
            let row = grievanceTableBody.insertRow();
            row.insertCell(0).textContent = grievance.id;
            row.insertCell(1).textContent = grievance.description;
            row.insertCell(2).textContent = grievance.status;
            row.insertCell(3).textContent = grievance.date;
        });
    })
    .catch(error => console.error('Error:', error));
}
