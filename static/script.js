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
// 🧠 DIRECT EXPLANATION SYSTEM (FIXED)
// ======================================================
 
function renderExplanation(id, explanations) {
    const el = document.getElementById(id);
    if (!el) return;

    if (el.dataset.rendered) return;

    el.innerHTML = `
        <div id="${id}-content">
            <p><b>🧠 Answer :</b> ${explanations.level1 || "Not Available"}</p>

            <p><b>🧠 Brief :</b><br>
            ${(explanations.level2 || "Not Available").replace(/\n/g, "<br>")}
            </p>

            <p><b>🧠 This Is The Final Mechanism:</b><br>
            ${(explanations.level3 || "Not Available").replace(/\n/g, "<br>")}
            </p>

            <p><b>🤖 AI Explanation:</b><br>
            ${(explanations.level4 || "AI Not Available").replace(/\n/g, "<br>")}
            </p>
        </div>
    `;

    el.dataset.rendered = "true";
}

// ======================================================
// 🤖 AI EXPLANATION (FIXED PAYLOAD)
// ======================================================
async function showAI(id, index, userAnswer) {
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
            body: JSON.stringify({
                q_index: index,
                user_answer: userAnswer
            })
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
