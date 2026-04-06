import os
import random
import re
import psycopg
import requests
from questions import all_questions
from flask import Flask, render_template, request, session, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")


# =========================================================
# 🧠 AI EXPLANATION
# =========================================================
def ai_explanation(question, correct):

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "AI Is Not Configured"

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "system",
                        "content": "Explain Clearly Step By Step With Formula And Logic"
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\nAnswer: {correct}"
                    }
                ]
            },
            timeout=10
        )

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        return "AI Is Currently Unavailable"

    except Exception:
        return "AI Is Currently Unavailable"


# =========================================================
# 🧠 EXPLANATION ENGINE
# =========================================================
def generate_explanation(q, user_answer=None):

    question = q.get("q", "")
    correct = str(q.get("answer", ""))

    exp = {
        "question": question,
        "level1": correct,
        "level2": "Solve Step By Step Using Basic Logic.",
        "level3": "Understand The Core Concept Behind The Question."
    }

    return exp


# =========================================================
# 🧠 XP + RANK
# =========================================================
def get_xp(diff):
    return {"easy": 5, "medium": 10, "hard": 20}.get(diff, 5)


def get_rank(xp):
    if xp >= 1000: return "Elite"
    if xp >= 600: return "Expert"
    if xp >= 300: return "Advanced"
    if xp >= 100: return "Intermediate"
    return "Beginner"


# =========================================================
# 🗄️ DB
# =========================================================
def get_db_connection():

    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("DATABASE_URL Not Set")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return psycopg.connect(db_url, sslmode="require")


# =========================================================
# 🌐 ROUTES
# =========================================================

@app.route('/', methods=['GET', 'POST'])
def login():

    # ✅ FIX: prevent logged-in users seeing login again
    if 'username' in session:
        return redirect('/quiz')

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
                cur.close()
                conn.close()
                return redirect('/quiz')
            else:
                cur.close()
                conn.close()
                return render_template("login.html", error="Wrong Password")

        else:
            hashed = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s,%s)",
                (username, hashed)
            )
            conn.commit()
            session['username'] = username

            cur.close()
            conn.close()

            return redirect('/quiz')

    return render_template("login.html")


@app.route('/quiz')
def quiz():

    if 'username' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT xp FROM users WHERE username=%s", (session['username'],))
    xp = cur.fetchone()[0]

    cur.close()
    conn.close()

    questions = random.sample(all_questions, 10)
    session['questions'] = questions

    return render_template("quiz.html", questions=questions)


# =========================================================
# ✅ SUBMIT
# =========================================================
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

    old_rank = get_rank(current_xp)
    new_rank = get_rank(new_xp)
    level_up = old_rank != new_rank

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

    session['level_up'] = level_up

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        wrong=wrong,
        xp_earned=xp_earned,
        new_xp=new_xp,
        rank=new_rank,
        level_up=level_up
    )


# =========================================================
# ✅ PROFILE
# =========================================================
@app.route('/profile')
def dashboard():

    if 'username' not in session:
        return redirect('/')

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT total_score, total_attempts, xp
        FROM users
        WHERE username=%s
    """, (username,))

    user = cur.fetchone()

    score = user[0] or 0
    attempts = user[1] or 0
    xp = user[2] or 0

    accuracy = round((score / attempts) * 100, 2) if attempts > 0 else 0

    cur.close()
    conn.close()

    level_up = session.pop('level_up', False)

    return render_template(
        'profile.html',
        username=username,
        xp=xp,
        rank=get_rank(xp),
        accuracy=accuracy,
        attempts=attempts,
        score=score,
        scores=[score],
        totals=[attempts],
        level_up=level_up
    )


# =========================================================
# 🏆 LEADERBOARD
# =========================================================
@app.route('/leaderboard')
def leaderboard():

    if 'username' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, xp, total_attempts
        FROM users
        ORDER BY xp DESC
        LIMIT 10
    """)

    users = cur.fetchall()

    data = []
    for u in users:
        rank = get_rank(u[1])
        data.append((u[0], u[1], u[2], rank))

    cur.close()
    conn.close()

    return render_template("leaderboard.html", data=data)


# =========================================================
# 🤖 AI ROUTE
# =========================================================
@app.route("/ai_explain", methods=["POST"])
def ai_explain():

    data = request.get_json()

    question = data.get("question", "")
    answer = data.get("answer", "")

    if not question:
        return jsonify({"explanation": "Invalid Question Data"})

    explanation = ai_explanation(question, answer)

    return jsonify({"explanation": explanation})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
