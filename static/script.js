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
// 🧠 DIRECT EXPLANATION SYSTEM (NO LEVELS)
// ======================================================
function renderExplanation(id, explanations) {
    const el = document.getElementById(id);
    if (!el) return;

    if (el.dataset.rendered) return; // prevent duplicate render

    el.innerHTML = `
        <div id="${id}-content">
            <p><b>🧠 Explanation 1:</b> ${explanations.level1 || "Not Available"}</p>

            <p><b>🧠 Explanation 2:</b><br>
            ${(explanations.level2 || "Not Available").replace(/\n/g, "<br>")}
            </p>

            <p><b>🧠 Explanation 3:</b><br>
            ${(explanations.level3 || "Not Available").replace(/\n/g, "<br>")}
            </p>

            <button onclick="showAI('${id}')" class="ai-btn">
                🤖 Explain With AI
            </button>

            <p id="${id}-ai"></p>
        </div>
    `;

    el.dataset.rendered = "true";
}


// ======================================================
// 🤖 AI EXPLANATION (CLEAN + SINGLE BUTTON)
// ======================================================
async function showAI(id) {
    const aiBox = document.getElementById(`${id}-ai`);

    if (!aiBox || aiBox.dataset.loading || aiBox.dataset.done) return;

    aiBox.dataset.loading = "true";
    aiBox.innerHTML = "<br><b>🤖 AI Explanation:</b><br>Generating...";

    try {
        const res = await fetch("/ai_explain", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ id: id })
        });

        const data = await res.json();

        aiBox.innerHTML =
            `<br><b>🤖 AI Explanation:</b><br>${data.explanation || "AI Not Available"}`;

    } catch (err) {
        aiBox.innerHTML =
            "<br><b>🤖 AI Explanation:</b><br>Error Fetching AI Explanation";
    }

    aiBox.dataset.loading = "false";
    aiBox.dataset.done = "true";
}
