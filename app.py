import os
import random
import re
import psycopg
from flask import Flask, render_template, request, session, jsonify

# =========================================================
# 🚀 FLASK APP
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# =========================================================
# 🧠 SMART EXPLANATION ENGINE
# =========================================================
def generate_explanations(question, answer, qtype):
    if qtype in ["quant", "di"]:
        return solve_quant(question, answer)
    elif qtype == "logic":
        return solve_logic(question, answer)
    elif qtype == "verbal":
        return solve_verbal(question, answer)
    return default_explanation(question, answer)

def solve_quant(question, answer):
    steps = []
    numbers = list(map(int, re.findall(r'\d+', question)))

    if "%" in question and "of" in question and len(numbers) >= 2:
        percent, total = numbers[0], numbers[1]
        result = (percent / 100) * total
        steps.append(f"Convert {percent}% → {percent}/100")
        steps.append(f"Multiply → ({percent}/100) × {total}")
        steps.append(f"Result = {result}")

    elif "+" in question:
        result = sum(numbers)
        steps.append(f"Add → {' + '.join(map(str, numbers))}")
        steps.append(f"Result = {result}")

    elif "×" in question:
        result = numbers[0] * numbers[1]
        steps.append(f"Multiply → {numbers[0]} × {numbers[1]}")
        steps.append(f"Result = {result}")

    elif "÷" in question or "divided" in question.lower():
        result = numbers[0] / numbers[1]
        steps.append(f"Divide → {numbers[0]} ÷ {numbers[1]}")
        steps.append(f"Result = {result}")

    else:
        steps.append("Understand Problem")
        steps.append(f"Answer = {answer}")

    return build_levels(steps, answer)

def solve_logic(question, answer):
    steps = []
    nums = list(map(int, re.findall(r'\d+', question)))

    if len(nums) >= 3:
        diff = nums[1] - nums[0]

        if all(nums[i+1] - nums[i] == diff for i in range(len(nums)-1)):
            steps.append(f"Pattern: +{diff}")
            steps.append(f"Next = {nums[-1]} + {diff}")

        elif nums[1] != 0 and nums[2] // nums[1] == nums[1] // nums[0]:
            ratio = nums[1] // nums[0]
            steps.append(f"Pattern: ×{ratio}")
            steps.append(f"Next = {nums[-1]} × {ratio}")

        else:
            steps.append("Complex Pattern")

    steps.append(f"Answer = {answer}")
    return build_levels(steps, answer)

def solve_verbal(question, answer):
    steps = []

    if "___" in question:
        steps.append("Check Subject")
        steps.append("Match Verb")

    elif "synonym" in question.lower():
        steps.append("Find Similar Meaning")

    elif "antonym" in question.lower():
        steps.append("Find Opposite Meaning")

    steps.append(f"Answer = {answer}")
    return build_levels(steps, answer)

def build_levels(steps, answer):
    return {
        "level1": " | ".join(steps[:2]),
        "level2": "\n".join(steps),
        "level3": "\n".join(["👉 " + s for s in steps] + [f"Final Answer: {answer} ✅"])
    }

def default_explanation(question, answer):
    return {
        "level1": f"Logic → {answer}",
        "level2": f"Step By Step → {answer}",
        "level3": f"Simple Thinking → {answer}"
    }

# =========================================================
# 📊 QUESTIONS
# =========================================================
all_questions = [
    {
        "q": "What Is The Main Cause Of SDK Usage Error?",
        "options": ["Incorrect API Key", "Network Issue", "Unsupported Version"],
        "answer": "Incorrect API Key",
        "type": "logic",
        "difficulty": "easy"
    },
    {
        "q": "How Can You Verify API Key Validity?",
        "options": ["Use SDK Test Method", "Guess Randomly", "Ignore It"],
        "answer": "Use SDK Test Method",
        "type": "logic",
        "difficulty": "easy"
    },
    {
        "q": "What Should You Do If SDK Version Is Unsupported?",
        "options": ["Update SDK", "Downgrade App", "Ignore Warning"],
        "answer": "Update SDK",
        "type": "logic",
        "difficulty": "medium"
    },
    {
        "q": "How Can Network Issues Affect SDK Usage?",
        "options": ["Timeout Errors", "Incorrect Results", "App Crash"],
        "answer": "Timeout Errors",
        "type": "logic",
        "difficulty": "medium"
    },
    {
        "q": "What Is The Recommended Way To Handle SDK Authentication?",
        "options": ["Hardcode Keys", "Use Environment Variables", "Ignore Auth"],
        "answer": "Use Environment Variables",
        "type": "logic",
        "difficulty": "hard"
    },
    {
        "q": "How Do You Debug Unexpected SDK Exceptions?",
        "options": ["Check Logs", "Restart App Only", "Ignore Error"],
        "answer": "Check Logs",
        "type": "logic",
        "difficulty": "hard"
    }
]

def get_questions():
    random.shuffle(all_questions)
    selected = all_questions[:5]

    for i, q in enumerate(selected):
        q["id"] = i

    return selected

# =========================================================
# 🗄️ DATABASE (RENDER FIXED)
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL Not Set")

    # 🔥 IMPORTANT FIX FOR RENDER (postgres:// → postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(db_url, sslmode='require')


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
            username TEXT,
            score INTEGER,
            total INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


try:
    init_db()
except Exception as e:
    print("DB ERROR:", e)

# =========================================================
# 🌐 ROUTES
# =========================================================
@app.route('/')
def home():
    return render_template("home.html")


@app.route('/quiz', methods=['POST'])
def quiz():
    session['username'] = request.form.get('username', 'Guest')
    questions = get_questions()
    session['questions'] = questions
    return render_template("quiz.html", questions=questions)


@app.route('/answer', methods=['POST'])
def answer():
    data = request.json
    qid = data.get("id")
    user_answer = data.get("answer")

    questions = session.get('questions', [])
    q = next((q for q in questions if q.get("id") == qid), None)

    if not q:
        return jsonify({"error": "Question Not Found"}), 400

    correct = q["answer"] == user_answer
    response = {"correct": correct}

    if not correct:
        response["explanation"] = generate_explanations(q["q"], q["answer"], q["type"])

    return jsonify(response)


@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get('questions', [])
    username = session.get('username', 'Guest')

    score = 0
    wrong = []

    for i, q in enumerate(questions):
        ans = request.form.get(f"q{i}")

        if ans == q["answer"]:
            score += 1
        else:
            wrong.append({
                "q": q["q"],
                "correct": q["answer"],
                "exp": generate_explanations(q["q"], q["answer"], q["type"])
            })

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO results (username, score, total) VALUES (%s, %s, %s)",
        (username, score, len(questions))
    )

    conn.commit()
    cur.close()
    conn.close()

    return render_template("result.html", score=score, total=len(questions), wrong=wrong)


@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT score, total FROM results ORDER BY id ASC")
    data = cur.fetchall()

    cur.close()
    conn.close()

    scores = [d[0] for d in data]
    totals = [d[1] for d in data]

    attempts = len(scores)
    avg_score = round(sum(scores)/attempts, 2) if attempts else 0

    return render_template(
        "dashboard.html",
        scores=scores,
        totals=totals,
        attempts=attempts,
        avg_score=avg_score
    )


@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, score, total
        FROM results
        ORDER BY score DESC, timestamp ASC
        LIMIT 10
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("leaderboard.html", data=data)

# =========================================================
# ▶ RUN (RENDER SAFE)
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
