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
# 🧠 EXPLANATION ENGINE
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
    return {
        "level1": f"Idea: {steps[0]}\nFinal Answer: {answer}",
        "level2": "\n\n".join(
            ["Step-By-Step Solution:"]
            + [f"{i+1}. {s}" for i, s in enumerate(steps)]
            + [f"\nConclusion: {answer}"]
        ),
        "level3": "Concept:\n\n" + "\n".join(steps)
    }

# =========================================================
# 🔢 SOLVERS
# =========================================================
def solve_quant(question, answer):
    steps = []

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
    return build_levels(steps, answer)

def solve_logic(question, answer):
    steps = []
    nums = list(map(float, re.findall(r'\d+\.?\d*', question)))

    if len(nums) >= 3:
        diff = nums[1] - nums[0]

        if all(nums[i+1] - nums[i] == diff for i in range(len(nums)-1)):
            steps.append(f"Constant Difference (+{diff})")
        else:
            steps.append("Pattern Analysis Required")
    else:
        steps.append("Logical Pattern Identification")

    steps.append(f"Correct Answer: {answer}")
    return build_levels(steps, answer)

def solve_verbal(question, answer):
    return build_levels(["Apply Grammar Or Meaning Logic", f"Final Answer: {answer}"], answer)

def default_explanation(question, answer):
    return build_levels(["Understand And Solve Step By Step"], answer)

# =========================================================
# 📊 QUESTIONS
# =========================================================
all_questions = [
    # YOUR DATA HERE
]

def get_xp(difficulty):
    return {"easy": 5, "medium": 10, "hard": 20}.get(difficulty, 5)

def get_questions(user_xp):
    if user_xp < 100:
        level = "easy"
    elif user_xp < 300:
        level = "medium"
    else:
        level = "hard"

    filtered = [q for q in all_questions if q["difficulty"] == level]
    random.shuffle(filtered)

    selected = filtered[:10]

    selected_with_ids = []
    for i, q in enumerate(selected):
        q_copy = q.copy()
        q_copy["id"] = i
        selected_with_ids.append(q_copy)

    return selected_with_ids

# =========================================================
# 🗄️ DATABASE
# =========================================================
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL Not Set")

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
            xp INTEGER DEFAULT 0
        )
    """)

    # ✅ THIS LINE FIXES YOUR ERROR
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0")

    conn.commit()
    cur.close()
    conn.close()

init_db()

# =========================================================
# 🔧 AUTO FIX MISSING COLUMNS
# =========================================================
def fix_missing_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    # Add 'xp' column if it does not exist
    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0
    """)
    conn.commit()
    cur.close()
    conn.close()

fix_missing_columns()

# =========================================================
# 🏆 RANK SYSTEM
# =========================================================
def get_rank(xp):
    if xp >= 1000: return "Elite"
    elif xp >= 600: return "Expert"
    elif xp >= 300: return "Advanced"
    elif xp >= 100: return "Intermediate"
    else: return "Beginner"

# =========================================================
# 🌐 ROUTES
# =========================================================

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xp FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    xp = row[0] if row else 0
    cur.close()
    conn.close()

    questions = get_questions(xp)
    session['questions'] = questions

    return render_template("quiz.html", questions=questions)

@app.route('/quiz', methods=['POST'])
def quiz():
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xp FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    xp = row[0] if row and row[0] is not None else 0

    cur.close()
    conn.close()

    questions = get_questions(xp)
    session['questions'] = questions

    return render_template("quiz.html", questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get('questions', [])
    username = session.get('username')

    if not username:
        return redirect('/')

    score = 0
    xp_earned = 0
    wrong = []

    for i, q in enumerate(questions):
        ans = request.form.get(f"q{i}")

        if ans == q["answer"]:
            score += 1
            xp_earned += get_xp(q["difficulty"])
        else:
            wrong.append({
                "q": q["q"],
                "correct": q["answer"],
                "exp": generate_explanations(q["q"], q["answer"], q["type"])
            })

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET total_score = total_score + %s,
        total_attempts = total_attempts + %s,
        xp = xp + %s
    WHERE username = %s
""", (score, len(questions), xp_earned, username))

    cur.execute("""
        UPDATE users
        SET total_score = total_score + %s,
            total_attempts = total_attempts + %s,
            xp = %s
        WHERE username = %s
    """, (score, len(questions), new_xp, username))

    conn.commit()
    cur.close()
    conn.close()

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        wrong=wrong,
        xp_earned=xp_earned,
        new_xp=new_xp,
        rank=get_rank(new_xp)
    )

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT total_score, total_attempts, xp FROM users WHERE username=%s", (username,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    score, attempts, xp = row if row else (0, 0, 0)

    accuracy = round((score / attempts) * 100, 2) if attempts else 0

    return render_template(
        "dashboard.html",
        username=username,
        score=score,
        attempts=attempts,
        accuracy=accuracy,
        rank=get_rank(xp),
        xp=xp
    )

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, xp, total_attempts FROM users ORDER BY xp DESC LIMIT 10")
    data = cur.fetchall()

    leaderboard_data = [(u[0], u[1], u[2], get_rank(u[1])) for u in data]

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
