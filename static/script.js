let t = 90;

let interval = setInterval(() => {
    t--;

    let minutes = Math.floor(t / 60);
    let seconds = t % 60;

    document.getElementById("timer").innerText =
        `Time Left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

    if (t <= 10) {
        document.getElementById("timer").style.color = "red";
    }

    if (t <= 0) {
        clearInterval(interval);
        document.forms[0].submit();
    }
}, 1000);


// 🔥 Smart Explanation Viewer

function showExplanation(level, id, explanations) {
    const el = document.getElementById(id);

    // Store data globally once
    if (!window.explanationsStore) {
        window.explanationsStore = {};
    }
    window.explanationsStore[id] = explanations;

    if (level === 1) {
        el.innerHTML = `
            <b>🧠 Level 1:</b> ${explanations.level1}
            <br><br>
            <button onclick="showExplanation(2, '${id}', window.explanationsStore['${id}'])">
                Explain More 🔍
            </button>
        `;
    }

    else if (level === 2) {
        el.innerHTML = `
            <b>🧠 Level 2:</b><br>${explanations.level2.replace(/\n/g, "<br>")}
            <br><br>
            <button onclick="showExplanation(3, '${id}', window.explanationsStore['${id}'])">
                Explain Like Beginner 👶
            </button>
        `;
    }

    else if (level === 3) {
        el.innerHTML = `
            <b>🧠 Level 3:</b><br>${explanations.level3.replace(/\n/g, "<br>")}
        `;
    }
}
