import os
import random
import re
import psycopg
import requests
from questions import all_questions
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# =========================================================
# 🚀 APP CONFIG
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")


# =========================================================
# 🧠 AI EXPLANATION (SAFE VERSION)
# =========================================================
def ai_explanation(question, correct):

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "AI Not Configured"

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Explain This Step By Step:\n{question}\nAnswer: {correct}"
                    }
                ]
            },
            timeout=6
        )

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        return "AI Failed"

    except Exception:
        return "AI Timeout"


# =========================================================
# 🧠 EXPLANATION ENGINE
# =========================================================
def generate_explanation(q, user_answer=None):

    question = q.get("q", "")
    correct = q.get("answer", "")
    qtype = q.get("type", "")
    subtype = q.get("subtype", "")

    nums = list(map(int, re.findall(r'\d+', question)))

    why_wrong = ""
    if user_answer and user_answer != correct:
        why_wrong = f"Your Answer: {user_answer}\nCorrect: {correct}\nCheck Concept"

    # ===== QUANT =====
    if qtype == "quant":

        if subtype == "percentage" and len(nums) >= 2:
            p, v = nums[0], nums[1]
            return {
                "level1": correct,
                "level2": f"{p}% of {v} = {(p/100)*v}",
                "level3": "Formula: (P/100)*Value",
                "level4": ai_explanation(question, correct),
                "why_wrong": why_wrong
            }

        if subtype == "average" and nums:
            return {
                "level1": correct,
                "level2": f"Avg = {sum(nums)}/{len(nums)}",
                "level3": "Average = Sum / Count",
                "level4": ai_explanation(question, correct),
                "why_wrong": why_wrong
            }

    # ===== DEFAULT =====
    return {
        "level1": correct,
        "level2": "Apply Logic",
        "level3": "Break Stepwise",
        "level4": ai_explanation(question, correct),
        "why_wrong": why_wrong
    }


# =========================================================
# 🧠 XP SYSTEM
# =========================================================
def get_xp(diff):
    return {"easy": 5, "medium": 10, "hard": 20}.get(diff, 5)


def get_questions(user_xp):

    level = "easy" if user_xp < 100 else "medium" if user_xp < 300 else "hard"

    filtered = [q for q in all_questions if q.get("difficulty") == level]

    if not filtered:
        filtered = all_questions  # fallback safety

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
        raise Exception("DATABASE_URL Missing")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg.connect(db_url, sslmode="require")


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

    conn.commit()
    cur.close()
    conn.close()


init_db()


# =========================================================
# 🏆 RANK
# =========================================================
def get_rank(xp):
    if xp >= 1000: return "Elite"
    if xp >= 600: return "Expert"
    if xp >= 300: return "Advanced"
    if xp >= 100: return "Intermediate"
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
                return redirect('/quiz')
        else:
            hashed = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s,%s)",
                (username, hashed)
            )
            conn.commit()
            session['username'] = username
            return redirect('/quiz')

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")


@app.route('/quiz')
def quiz():

    if 'username' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT xp FROM users WHERE username=%s", (session['username'],))
    xp = cur.fetchone()[0]

    questions = get_questions(xp)
    session['questions'] = questions

    return render_template("quiz.html", questions=questions)


@app.route('/submit', methods=['POST'])
def submit():

    questions = session.get('questions', [])
    username = session.get('username')

    if not questions or not username:
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
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html')


@app.route('/leaderboard')
def leaderboard():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, xp, total_score
        FROM users
        ORDER BY xp DESC
        LIMIT 10
    """)

    users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('leaderboard.html', users=users)


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
