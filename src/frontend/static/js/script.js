function allowDrop(event) {
    event.preventDefault();
}

function drag(event) {
    const employee = event.target.dataset.employee;
    const time = event.target.dataset.time;
    const days = event.target.dataset.days;

    event.dataTransfer.setData("employee", employee);
    event.dataTransfer.setData("time", time);
    event.dataTransfer.setData("days", days);
}

function drop(event) {
    event.preventDefault();

    const dayCard = event.target.closest(".day-card");

    if (!dayCard) {
        return;
    }

    const droppedDay = dayCard.dataset.day;
    const employee = event.dataTransfer.getData("employee");
    const time = event.dataTransfer.getData("time");
    const availableDays = event.dataTransfer.getData("days");

    // Check if employee is available on that day
    if (!availableDays.includes(droppedDay)) {
        alert(`${employee} is not available on ${droppedDay}.`);
        return;
    }

    // Prevent duplicate employee in same day
    const existingShifts = dayCard.querySelectorAll(".shift-card span");

    for (let shift of existingShifts) {
        if (shift.textContent.trim() === employee) {
            alert(`${employee} is already scheduled on ${droppedDay}.`);
            return;
        }
    }

    const newShift = document.createElement("div");
    newShift.className = "shift-card new-shift";
    newShift.innerHTML = `
        <strong>${time}</strong>
        <span>${employee}</span>
    `;

    dayCard.appendChild(newShift);
}

function createSuggestedSchedule() {
    alert("Suggested schedule feature coming next 🚀");

    // Later this will:
    // 1. Read staff availability
    // 2. Auto-assign employees to days
    // 3. Populate the schedule
}

let originalRows = [];

function filterShifts() {
    const input = document.getElementById("shiftSearch");
    const filter = input.value.toLowerCase().trim();

    const tbody = document.querySelector("#shiftTable tbody");

    // Store original rows ONLY once
    if (originalRows.length === 0) {
        originalRows = Array.from(tbody.querySelectorAll("tr"));
    }

    const rows = Array.from(tbody.querySelectorAll("tr"));

    // If empty → restore original order
    if (filter === "") {
        tbody.innerHTML = "";
        originalRows.forEach(row => {
            row.style.display = "";
            tbody.appendChild(row);
        });
        return;
    }

    function getScore(text) {
        if (text === filter) return 3;
        if (text.startsWith(filter)) return 2;
        if (text.includes(filter)) return 1;
        return 0;
    }

    const scoredRows = rows.map(row => {
        const employee = row.cells[0].textContent.toLowerCase();
        const day = row.cells[1].textContent.toLowerCase();

        const score = Math.max(getScore(employee), getScore(day));
        return { row, score };
    });

    const filtered = scoredRows
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score);

    tbody.innerHTML = "";

    filtered.forEach(item => {
        item.row.style.display = "";
        tbody.appendChild(item.row);
    });
}