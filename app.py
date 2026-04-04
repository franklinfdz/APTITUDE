import os
import random
import re
import psycopg
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# =========================================================
# 🚀 FLASK APP
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# =========================================================
# 🧠 EXPLANATION ENGINE (AS GIVEN - NO CHANGE)
# =========================================================
def generate_explanation(q, user_answer=None):
    question = q.get("q", "")
    correct = q.get("answer", "")
    qtype = q.get("type", "")
    difficulty = q.get("difficulty", "easy")

    def join_steps(steps):
        return "\n".join(steps)

    why_wrong = ""
    if user_answer and user_answer != correct:
        why_wrong = join_steps([
            f"Your Answer: {user_answer}",
            f"Correct Answer: {correct}",
            "",
            "Why This Is Wrong:",
            "You Likely Misread The Question Or Applied Incorrect Logic.",
            "Recheck The Steps And Focus On The Correct Method."
        ])

    concept = ""

    if qtype == "quant":
        if "%" in question:
            concept = "Percentage = (Part / Whole) × 100"
        elif "average" in question.lower():
            concept = "Average = Total Sum / Number Of Values"
        elif "ratio" in question.lower():
            concept = "Ratio = Comparison Of Two Quantities"
        elif "speed" in question.lower():
            concept = "Speed = Distance / Time"
        elif "interest" in question.lower():
            concept = "Interest Depends On Principal, Rate And Time"
        else:
            concept = "Basic Arithmetic Operations"

        level1 = f"Answer = {correct}"

        level2 = join_steps([
            "Step 1: Understand The Question",
            "Step 2: Identify Required Formula Or Operation",
            "Step 3: Apply Values Carefully",
            f"Final Answer = {correct}"
        ])

        level3 = join_steps([
            "Let’s Understand This Clearly:",
            "",
            "First, Identify What The Question Is Asking.",
            "Then Select The Correct Formula Or Logic.",
            "",
            f"Apply The Steps Carefully To Reach {correct}.",
            "",
            "Always Double-Check Calculations To Avoid Mistakes."
        ])

    elif qtype == "logic":

        concept = "Pattern Recognition And Logical Thinking"

        level1 = f"Answer = {correct}"

        level2 = join_steps([
            "Step 1: Observe Pattern Carefully",
            "Step 2: Identify Rule (Increase / Multiply / Mix)",
            "Step 3: Apply Pattern",
            f"Final Answer = {correct}"
        ])

        level3 = join_steps([
            "Let’s Break This Down:",
            "",
            "Every Logical Question Follows A Pattern.",
            "Your Job Is To Find That Pattern Step By Step.",
            "",
            "Once You Understand The Rule,",
            "Apply It Consistently To Get The Answer.",
            "",
            f"This Leads To {correct}."
        ])

    elif qtype == "verbal":

        concept = "Grammar, Vocabulary And Sentence Logic"

        level1 = f"Answer = {correct}"

        level2 = join_steps([
            "Step 1: Read Carefully",
            "Step 2: Understand Meaning Or Grammar Rule",
            "Step 3: Eliminate Wrong Options",
            f"Correct Answer = {correct}"
        ])

        level3 = join_steps([
            "Let’s Understand This:",
            "",
            "Language Questions Test Meaning And Structure.",
            "You Must Understand Context Before Choosing.",
            "",
            "Eliminate Options That Don’t Fit.",
            f"Correct Option Is {correct}."
        ])

    else:
        concept = "General Problem Solving"
        level1 = f"Answer = {correct}"
        level2 = f"Apply Correct Logic → {correct}"
        level3 = f"Break Down Problem Step By Step → {correct}"

    return {
        "level1": level1,
        "level2": level2,
        "level3": level3,
        "concept": concept,
        "why_wrong": why_wrong
    }

# =========================================================
# 📊 QUESTIONS (EMPTY - YOU ADD LATER)
# =========================================================
all_questions = []

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

    for i, q in enumerate(selected):
        q["id"] = i

    return selected

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

    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0")

    conn.commit()
    cur.close()
    conn.close()

init_db()

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
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect('/quiz')

        elif not user:
            hashed_pw = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_pw)
            )
            conn.commit()
            session['username'] = username
            return redirect('/quiz')

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

@app.route('/quiz')
def quiz():
    username = session.get('username')
    if not username:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xp FROM users WHERE username=%s", (username,))
    xp = cur.fetchone()[0]
    cur.close()
    conn.close()

    questions = get_questions(xp)
    session['questions'] = questions

    return render_template("quiz.html", questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get('questions', [])
    username = session.get('username')

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
                "exp": generate_explanation(q, ans)
            })

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT xp FROM users WHERE username=%s", (username,))
    current_xp = cur.fetchone()[0]

    new_xp = current_xp + xp_earned

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
    score, attempts, xp = cur.fetchone()

    cur.close()
    conn.close()

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
