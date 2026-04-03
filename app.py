import os
import random
import re
import psycopg
from flask import Flask, render_template, request, session, jsonify, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# =========================================================
# 🚀 FLASK APP
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# =========================================================
# ⚡ XP SYSTEM
# =========================================================
XP_MAP = {
    "easy": 1,
    "medium": 2,
    "hard": 3
}

# =========================================================
# 🧠 EXPLANATION ENGINE (UNCHANGED CORE)
# =========================================================
def generate_explanations(question, answer, qtype):
    try:
        qtype = (qtype or "").lower().strip()
        q_lower = question.lower()

        if qtype in ["quant", "di"]:
            return solve_quant(question, answer)

        elif qtype == "logic":
            return solve_logic(question, answer)

        elif qtype == "verbal":
            return solve_verbal(question, answer)

        if any(sym in question for sym in ["%", "+", "-", "×", "÷"]):
            return solve_quant(question, answer)

        if re.search(r'\d+', question) and any(word in q_lower for word in ["series", "next", "missing"]):
            return solve_logic(question, answer)

        if any(word in q_lower for word in ["synonym", "antonym", "fill", "spelling"]):
            return solve_verbal(question, answer)

        return default_explanation(question, answer)

    except Exception as e:
        print("EXPLANATION ERROR:", e)
        return default_explanation(question, answer)

# =========================================================
# 🧩 LEVEL BUILDER
# =========================================================
def build_levels(steps, answer, question=""):
    level1 = f"Idea: {steps[0]}\nFinal Answer: {answer}"

    level2_lines = ["Step-By-Step Solution:"]
    for i, s in enumerate(steps):
        level2_lines.append(f"{i+1}. {s}")
    level2_lines.append(f"\nConclusion: {answer}")

    level3 = "Concept:\n\n" + "\n".join(steps)

    return {
        "level1": level1,
        "level2": "\n\n".join(level2_lines),
        "level3": level3
    }

# =========================================================
# 🔢 QUANT / LOGIC / VERBAL (SAFE VERSION)
# =========================================================
def solve_quant(question, answer):
    steps = []
    numbers = list(map(float, re.findall(r'\d+\.?\d*', question)))

    if "%" in question:
        steps.append("Convert Percentage And Multiply")

    elif "+" in question:
        steps.append("Perform Addition")

    elif "-" in question:
        steps.append("Perform Subtraction")

    elif "×" in question or "x" in question.lower():
        steps.append("Perform Multiplication")

    elif "÷" in question or "divided" in question.lower():
        steps.append("Perform Division")

    else:
        steps.append("Break Down Problem Logically")

    steps.append(f"Final Result = {answer}")
    return build_levels(steps, answer, question)

def solve_logic(question, answer):
    steps = []
    nums = list(map(float, re.findall(r'\d+\.?\d*', question)))

    if len(nums) >= 3:
        diff = nums[1] - nums[0]

        if all(nums[i+1] - nums[i] == diff for i in range(len(nums)-1)):
            steps.append(f"Constant Difference (+{diff})")

        elif all(nums[i] != 0 and nums[i+1] % nums[i] == 0 for i in range(len(nums)-1)):
            ratio = nums[1] / nums[0]
            steps.append(f"Multiplicative Pattern (×{ratio})")

        else:
            steps.append("Pattern Analysis Required")

    else:
        steps.append("Logical Pattern Identification")

    steps.append(f"Correct Answer: {answer}")
    return build_levels(steps, answer, question)

def solve_verbal(question, answer):
    steps = ["Apply Grammar Or Meaning Logic", f"Final Answer: {answer}"]
    return build_levels(steps, answer, question)

def default_explanation(question, answer):
    return build_levels(["Understand And Solve Step By Step"], answer, question)

# =========================================================
# 📊 QUESTIONS (KEEP YOUR FULL DATA)
# =========================================================
all_questions = [
    # KEEP YOUR FULL QUESTION LIST HERE (UNCHANGED)
]


def get_user_level(xp):
    if xp < 50:
        return "easy"
    elif xp < 150:
        return "medium"
    else:
        return "hard"


def get_questions(user_xp=0):
    level = get_user_level(user_xp)

    easy = [q for q in all_questions if q["difficulty"] == "easy"]
    medium = [q for q in all_questions if q["difficulty"] == "medium"]
    hard = [q for q in all_questions if q["difficulty"] == "hard"]

    if level == "easy":
        selected = (
            random.sample(easy, 7) +
            random.sample(medium, 3)
        )

    elif level == "medium":
        selected = (
            random.sample(easy, 3) +
            random.sample(medium, 5) +
            random.sample(hard, 2)
        )

    else:  # HARD LEVEL
        selected = (
            random.sample(medium, 4) +
            random.sample(hard, 6)
        )

    random.shuffle(selected)

    for i, q in enumerate(selected):
        q["id"] = i

    return selected


# =========================================================
# 🗄️ DATABASE
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg.connect(db_url, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            total_score INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            total_xp INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =========================================================
# 🏆 RANK SYSTEM (XP BASED)
# =========================================================
def get_rank(xp):
    if xp >= 500:
        return "Elite"
    elif xp >= 250:
        return "Pro"
    elif xp >= 100:
        return "Advanced"
    elif xp >= 50:
        return "Intermediate"
    else:
        return "Beginner"

# =========================================================
# 🌐 ROUTES
# =========================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user:
            if check_password_hash(user[2], password):
                session['username'] = username
                return redirect('/dashboard')
            else:
                return render_template("login.html", error="Invalid Credentials")
        else:
            hashed_pw = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_pw)
            )
            conn.commit()

            session['username'] = username
            return redirect('/dashboard')

    return render_template("login.html")

@app.route('/quiz', methods=['POST'])
def quiz():
    username = session.get('username')

    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT total_xp FROM users WHERE username=%s", (username,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    user_xp = user[0] if user else 0

    questions = get_questions(user_xp)
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

    return jsonify({
        "correct": correct,
        "correct_answer": q["answer"],
        "type": q["type"]
    })

@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get('questions', [])
    username = session.get('username')

    if not questions or not username:
        return redirect('/')

    score = 0
    xp_earned = 0

    for i, q in enumerate(questions):
        ans = request.form.get(f"q{i}")
        if ans == q["answer"]:
            score += 1
            xp_earned += XP_MAP.get(q["difficulty"], 1)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET total_score = total_score + %s,
            total_attempts = total_attempts + %s,
            total_xp = total_xp + %s
        WHERE username = %s
    """, (score, len(questions), xp_earned, username))

    conn.commit()
    cur.close()
    conn.close()

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        xp=xp_earned
    )

@app.route('/dashboard')
def dashboard():
    username = session.get('username')

    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT total_score, total_attempts, total_xp
        FROM users
        WHERE username = %s
    """, (username,))

    user = cur.fetchone()
    cur.close()
    conn.close()

    score, attempts, xp = user
    accuracy = round((score / attempts) * 100, 2) if attempts else 0
    rank = get_rank(xp)

    return render_template(
        "dashboard.html",
        username=username,
        score=score,
        attempts=attempts,
        accuracy=accuracy,
        xp=xp,
        rank=rank
    )

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, total_score, total_attempts, total_xp
        FROM users
        ORDER BY total_xp DESC
        LIMIT 10
    """)

    data = cur.fetchall()

    leaderboard_data = []
    for user in data:
        rank = get_rank(user[3])
        leaderboard_data.append((user[0], user[1], user[2], user[3], rank))

    cur.close()
    conn.close()

    return render_template("leaderboard.html", data=leaderboard_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =========================================================
# ▶ RUN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
