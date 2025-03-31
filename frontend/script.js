const socket = io("http://localhost:5050");

const nameInput = document.getElementById("nameInput");
const nameList = document.getElementById("nameList");
const drawResult = document.getElementById("drawResult");
const registrationSection = document.getElementById("registrationSection");
const resultsSection = document.getElementById("resultsSection");

const pastSubmissionsContainer = document.getElementById('pastSubmissions');

// Load past submissions from local storage
let pastSubmissions = JSON.parse(localStorage.getItem('pastSubmissions')) || [];

// Function to render past submissions as buttons
function renderPastSubmissions() {
    pastSubmissionsContainer.innerHTML = '';
    pastSubmissions.forEach((name, index) => {
        const buttonContainer = document.createElement('div');
        buttonContainer.style.display = 'inline-flex';
        buttonContainer.style.alignItems = 'center';

        const nameButton = document.createElement('button');
        nameButton.textContent = name;
        nameButton.addEventListener('click', () => {
            registerName(name);
        });

        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'X';
        deleteButton.classList.add('delete-btn');
        deleteButton.addEventListener('click', () => {
            pastSubmissions.splice(index, 1);
            localStorage.setItem('pastSubmissions', JSON.stringify(pastSubmissions));
            renderPastSubmissions();
        });

        buttonContainer.appendChild(nameButton);
        buttonContainer.appendChild(deleteButton);
        pastSubmissionsContainer.appendChild(buttonContainer);
    });
}

// Function to register a name
function registerName(name) {
    pastSubmissions = pastSubmissions.filter(submission => submission !== name);
    pastSubmissions.unshift(name);
    localStorage.setItem('pastSubmissions', JSON.stringify(pastSubmissions));
    renderPastSubmissions();

    socket.emit("register_name", name);
}

// Initial render of past submissions
renderPastSubmissions();

function showRegistrationSection() {
    registrationSection.style.display = "block";
    resultsSection.style.display = "none";
}

function showResultsSection() {
    registrationSection.style.display = "none";
    resultsSection.style.display = "block";
}

socket.on("update_names", (names) => {
    nameList.innerHTML = "";
    names.forEach((name) => {
        const li = document.createElement("li");
        li.textContent = name;
        nameList.appendChild(li);
    });
});

socket.on("draw_result", (names) => {
    drawResult.innerHTML = "";
    if (names.length === 0) {
        const noParticipantsMessage = document.createElement("p");
        noParticipantsMessage.textContent = "לא היו נרשמים";
        drawResult.appendChild(noParticipantsMessage);
    } else {
        names.forEach((name) => {
            const li = document.createElement("li");
            li.textContent = name;
            drawResult.appendChild(li);
        });
    }
});

socket.on("draw_time", (drawTime) => {
    if (typeof drawTime === "number") {
        const drawDate = new Date(drawTime * 1000);
        const formattedDate = drawDate.toLocaleDateString("he-IL");
        const formattedTime = drawDate.toLocaleTimeString("he-IL", { hour: '2-digit', minute: '2-digit' });
        const drawDateTimeElement = document.getElementById("drawDateTime");
        drawDateTimeElement.textContent = `הגרלה ב- ${formattedDate} בשעה ${formattedTime}`;
        updateCountdown(drawTime);
    }
});

socket.on("error", (err) => {
    alert(err.message || "אירעה שגיאה");
});

document.getElementById("registerForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const name = nameInput.value.trim();
    if (name) {
        registerName(name);
        nameInput.value = "";
    }
});

// Countdown logic
let timer; // Make the timer global

function updateCountdown(drawTime) {
    if (timer) {
        clearInterval(timer); // Clear the existing timer
    }

    function refresh() {
        const now = Math.floor(Date.now() / 1000);
        const diff = drawTime - now;
        const el = document.getElementById("countdown");

        if (diff <= 0) {
            el.textContent = "ההגרלה מתבצעת כעת!";
            clearInterval(timer);
            showResultsSection();
        } else {
            const hours = Math.floor(diff / 3600);
            const minutes = Math.floor((diff % 3600) / 60);
            const seconds = diff % 60;
            el.textContent = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            showRegistrationSection();
        }
    }

    timer = setInterval(refresh, 1000);
    refresh();
}
