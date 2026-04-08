const timerEl = document.getElementById("timer");

if (timerEl) {

    let t = 90;

    let interval = setInterval(() => {
        t--;

        let minutes = Math.floor(t / 60);
        let seconds = t % 60;

        timerEl.innerText =
            `Time Left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (t <= 10) {
            timerEl.style.color = "red";
        }

        if (t <= 0) {
            clearInterval(interval);
            document.forms[0]?.submit();
        }
    }, 1000);

}

// ======================================================
// 🔥 EXPLANATION SYSTEM (FIXED + UPGRADED)
// ======================================================
function showExplanation(level, id, explanations) {
    const el = document.getElementById(id);

    // Store Explanation Globally
    if (!window.expStore) {
        window.expStore = {};
    }
    window.expStore[id] = explanations;

    // Initialize Structure Once
    if (!el.dataset.initialized) {
        el.innerHTML = `
            <div id="${id}-content"></div>
            <div id="${id}-buttons"></div>
        `;
        el.dataset.initialized = "true";
    }

    const content = document.getElementById(`${id}-content`);
    const buttons = document.getElementById(`${id}-buttons`);

    // ================= LEVEL 1 =================
    if (level === 1) {
        content.innerHTML = `
            <b>🧠 Level 1:</b> ${explanations.level1}
        `;

        buttons.innerHTML = `
            <br>
            <button onclick="showExplanation(2, '${id}', window.expStore['${id}'])">
                Explain More 🔍
            </button>
        `;
    }

    // ================= LEVEL 2 =================
    else if (level === 2) {
        content.innerHTML += `
            <br><br>
            <b>🧠 Level 2:</b><br>
            ${explanations.level2.replace(/\n/g, "<br>")}
        `;

        buttons.innerHTML = `
            <br>
            <button onclick="showExplanation(3, '${id}', window.expStore['${id}'])">
                Explain Thoroughly 📘
            </button>
        `;
    }

    // ================= LEVEL 3 =================
    else if (level === 3) {
        content.innerHTML += `
            <br><br>
            <b>🧠 Level 3:</b><br>
            ${explanations.level3.replace(/\n/g, "<br>")}
        `;

        buttons.innerHTML = `
            <br>
            <button onclick="showAI('${id}')">
                🤖 AI Explain
            </button>
        `;
    }
}


// ======================================================
// 🤖 AI EXPLANATION (FINAL LEVEL)
// ======================================================
function showAI(id) {
    const exp = window.expStore[id];
    const content = document.getElementById(`${id}-content`);
    const buttons = document.getElementById(`${id}-buttons`);

    // Prevent Duplicate AI Injection
    if (content.dataset.aiShown) return;

    content.innerHTML += `
        <br><br>
        <b>🤖 AI Explanation:</b><br>
        ${exp.level4 ? exp.level4.replace(/\n/g, "<br>") : "No AI Explanation Available"}
    `;

    content.dataset.aiShown = "true";

    // Remove Button After Use
    buttons.innerHTML = "";
}
