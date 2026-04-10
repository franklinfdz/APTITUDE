// ======================================================
// ⏳ SMART TIMER (PERSISTENT + SAFE)
// ======================================================
const timerEl = document.getElementById("timer");

if (timerEl) {
    let t = sessionStorage.getItem("timeLeft")
        ? parseInt(sessionStorage.getItem("timeLeft"))
        : 90;

    let interval = setInterval(() => {
        t--;
        sessionStorage.setItem("timeLeft", t);

        let minutes = Math.floor(t / 60);
        let seconds = t % 60;

        timerEl.innerText =
            `Time Left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (t <= 10) {
            timerEl.style.color = "red";
        }

        if (t <= 0) {
            clearInterval(interval);
            sessionStorage.removeItem("timeLeft");
            document.forms[0]?.submit();
        }
    }, 1000);
}


// ======================================================
// 🧠 EXPLANATION SYSTEM (SAFE + OPTIMIZED)
// ======================================================
function showExplanation(level, id, explanations) {
    const el = document.getElementById(id);

    if (!window.expStore) window.expStore = {};
    window.expStore[id] = explanations;

    if (!el.dataset.initialized) {
        el.innerHTML = `
            <div id="${id}-content"></div>
            <div id="${id}-buttons"></div>
        `;
        el.dataset.initialized = "true";
    }

    const content = document.getElementById(`${id}-content`);
    const buttons = document.getElementById(`${id}-buttons`);

    // Prevent Duplicate Levels
    if (content.dataset[`level${level}`]) return;

    // ================= LEVEL 1 =================
    if (level === 1) {
        content.innerHTML = `
            <b>🧠 Level 1:</b> ${explanations.level1 || "Not Available"}
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
            ${(explanations.level2 || "Not Available").replace(/\n/g, "<br>")}
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
            ${(explanations.level3 || "Not Available").replace(/\n/g, "<br>")}
        `;

        buttons.innerHTML = `
            <br>
            <button onclick="showAI('${id}')">
                🤖 AI Explain
            </button>
        `;
    }

    content.dataset[`level${level}`] = "true";
}


// ======================================================
// 🤖 AI EXPLANATION (CONTROLLED + SAFE)
// ======================================================
async function showAI(id) {
    const content = document.getElementById(`${id}-content`);
    const buttons = document.getElementById(`${id}-buttons`);

    if (content.dataset.aiShown || content.dataset.loading) return;

    content.dataset.loading = "true";

    // Loading UI
    content.innerHTML += `
        <br><br>
        <b>🤖 AI Explanation:</b><br>
        <span id="${id}-loading">Generating...</span>
    `;

    try {
        const res = await fetch("/ai_explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id })
        });

        const data = await res.json();

        document.getElementById(`${id}-loading`).innerHTML =
            data.explanation || "AI Not Available";

    } catch (err) {
        document.getElementById(`${id}-loading`).innerHTML =
            "Error Fetching AI Explanation";
    }

    content.dataset.aiShown = "true";
    content.dataset.loading = "false";

    buttons.innerHTML = "";
}
