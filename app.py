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
    qtype = q.get("type", "")
    subtype = q.get("subtype", "")

    nums = list(map(float, re.findall(r'\d+\.?\d*', question)))

    # ================= WRONG FEEDBACK =================
    why_wrong = ""
    if user_answer and str(user_answer) != correct:
        why_wrong = f"Your Answer Was {user_answer}, But Correct Answer Is {correct}. Focus On The Core Concept Used Here."

    # ================= DEFAULT STRUCT =================
    exp = {
        "level1": correct,
        "level2": "",
        "level3": "",
        "level4": ai_explanation(question, correct),
        "why_wrong": why_wrong
    }

    # =========================================================
    # 🟢 QUANT SECTION
    # =========================================================
    if qtype == "quant":

        # 🔹 Percentage
        if "percent" in question.lower() or subtype.startswith("percentage"):
            if len(nums) >= 2:
                p, v = nums[0], nums[1]
                exp["level2"] = f"Convert {p}% Into Decimal → {p}/100. Then Multiply With {v}. That Gives {correct}."
                exp["level3"] = "Percentage Means A Part Out Of 100. First Convert Into Fraction, Then Multiply With The Number."
                return exp

        # 🔹 Average
        if "average" in question.lower():
            total = sum(nums)
            count = len(nums)
            exp["level2"] = f"Add All Values → {total}. Divide By Total Numbers ({count}). That Gives {correct}."
            exp["level3"] = "Average Means Equal Distribution. Add Everything And Divide Into Equal Parts."
            return exp

        # 🔹 Ratio
        if "ratio" in question.lower():
            exp["level2"] = "Convert Ratio Into Parts, Then Distribute Total Accordingly."
            exp["level3"] = "Ratio Splits A Quantity Into Proportions. Think Of Sharing Based On Given Parts."
            return exp

        # 🔹 Speed / Distance / Time
        if "speed" in question.lower():
            exp["level2"] = "Use Formula: Speed = Distance ÷ Time. Rearrange Based On What Is Asked."
            exp["level3"] = "Speed Tells How Fast Something Moves. Divide Distance By Time."
            return exp

        # 🔹 Interest
        if "interest" in question.lower():
            exp["level2"] = "Simple Interest = (P × R × T) / 100. Identify Principal, Rate, And Time From Question."
            exp["level3"] = "Interest Is Extra Money Earned Over Time. Multiply Principal, Rate, And Time."
            return exp

        # 🔹 LCM / HCF
        if "lcm" in question.lower():
            exp["level2"] = "Find Common Multiples Of Both Numbers And Pick The Smallest One."
            exp["level3"] = "LCM Means Smallest Number Divisible By Both Numbers."
            return exp

        if "hcf" in question.lower():
            exp["level2"] = "Find Common Factors And Pick The Greatest One."
            exp["level3"] = "HCF Means Largest Number That Divides Both."
            return exp

        # 🔹 Square / Cube / Root
        if "square root" in question.lower() or "√" in question:
            exp["level2"] = "Find Number Which Multiplied By Itself Gives The Given Value."
            exp["level3"] = "Square Root Is Opposite Of Squaring."
            return exp

        if "square" in question.lower() and nums:
            exp["level2"] = f"Multiply Number By Itself → Example: {nums[0]} × {nums[0]}."
            exp["level3"] = "Square Means Number Times Itself."
            return exp

        if "cube" in question.lower() and nums:
            exp["level2"] = f"Multiply Number Three Times → {nums[0]} × {nums[0]} × {nums[0]}."
            exp["level3"] = "Cube Means Multiply Number Three Times."
            return exp

        # 🔹 Profit / Loss
        if "profit" in question.lower() or "loss" in question.lower():
            exp["level2"] = "Profit = SP - CP. Profit% = (Profit / CP) × 100."
            exp["level3"] = "Profit Means Gain. Loss Means Losing Money."
            return exp

        # 🔹 Time & Work
        if "work" in question.lower():
            exp["level2"] = "Use Work Formula: Work = Rate × Time. Combine Efficiencies."
            exp["level3"] = "More Workers Means Less Time. Work Is Shared."
            return exp

        # 🔹 Clock
        if "clock" in question.lower():
            exp["level2"] = "Use Angle Formula: (Hour Hand - Minute Hand)."
            exp["level3"] = "Clock Angles Depend On Positions Of Hands."
            return exp

        # 🔹 Modulus / Remainder
        if "remainder" in question.lower():
            exp["level2"] = "Divide Number And Take What Is Left."
            exp["level3"] = "Remainder Is What Stays After Division."
            return exp

    # =========================================================
    # 🟡 LOGIC SECTION
    # =========================================================
    if qtype == "logic":

        if subtype in ["series", "pattern"]:
            exp["level2"] = "Check Pattern: Addition, Multiplication, Squares, Or Alternating Pattern."
            exp["level3"] = "Series Is Like A Puzzle Pattern. Find What Changes Between Numbers."
            return exp

        if subtype == "odd_one":
            exp["level2"] = "Compare All Options And Find One That Does Not Follow The Same Rule."
            exp["level3"] = "Odd One Out Means One Is Different."
            return exp

        if subtype == "coding":
            exp["level2"] = "Assign Numeric Values To Letters And Look For Pattern."
            exp["level3"] = "Each Letter Has A Value. Combine Them To Find Pattern."
            return exp

        if subtype == "alphabet":
            exp["level2"] = "Check Alphabet Positions And Pattern Between Letters."
            exp["level3"] = "Letters Follow A Sequence Like Numbers."
            return exp

    # =========================================================
    # 🔵 VERBAL SECTION
    # =========================================================
    if qtype == "verbal":

        if subtype == "grammar":
            exp["level2"] = "Apply Grammar Rules Based On Subject And Tense."
            exp["level3"] = "Grammar Is About Correct Sentence Structure."
            return exp

        if subtype == "synonym":
            exp["level2"] = "Find Word With Same Meaning."
            exp["level3"] = "Synonym Means Similar Meaning."
            return exp

        if subtype == "antonym":
            exp["level2"] = "Find Word With Opposite Meaning."
            exp["level3"] = "Antonym Means Opposite Meaning."
            return exp

        if subtype == "plural":
            exp["level2"] = "Apply Plural Rules Or Irregular Forms."
            exp["level3"] = "Plural Means More Than One."
            return exp

        if subtype == "spelling":
            exp["level2"] = "Check Correct Letter Arrangement Carefully."
            exp["level3"] = "Spelling Needs Attention To Detail."
            return exp

    # =========================================================
    # 🟣 DI SECTION
    # =========================================================
    if qtype == "di":
        exp["level2"] = "Analyze Given Data And Apply Percentage Or Ratio Logic."
        exp["level3"] = "DI Means Understanding Data And Calculating Step By Step."
        return exp

    # =========================================================
    # ⚪ FALLBACK
    # =========================================================
    exp["level2"] = "Break The Question Into Parts And Apply Basic Concepts Step By Step."
    exp["level3"] = "Think Calmly. Every Problem Has A Pattern Or Rule."

    return exp

# =========================================================
# 🧠 XP + RANK
# =========================================================
def get_xp(diff):
    return {"easy": 5, "medium": 10, "hard": 20}.get(diff, 5)


def get_rank(xp):
    if xp >= 2000: return "Legend"
    if xp >= 1500: return "Master"
    if xp >= 1000: return "Diamond"
    if xp >= 700: return "Platinum"
    if xp >= 400: return "Gold"
    if xp >= 200: return "Silver"
    return "Bronze"

def get_progress(xp):
    levels = [0, 200, 400, 700, 1000, 1500, 2000]

    for i in range(len(levels) - 1):
        if levels[i] <= xp < levels[i+1]:
            return int(((xp - levels[i]) / (levels[i+1] - levels[i])) * 100)

    return 100

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



def initialize_database():
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
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_scores (
        id SERIAL PRIMARY KEY,
        username TEXT,
        score INTEGER,
        total INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

# RUN ON STARTUP
initialize_database()


# =========================================================
# 🌐 ROUTES
# =========================================================

@app.route('/', methods=['GET', 'POST'])
def login():

    # ✅ FIX: prevent logged-in users seeing login again

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

    cur.execute("""
    INSERT INTO user_scores (username, score, total)
    VALUES (%s, %s, %s)
    """, (username, score, len(questions)))

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

    # 🔥 FETCH LAST 10 SCORES
    cur.execute("""
    SELECT score, total FROM user_scores
    WHERE username = %s
    ORDER BY created_at DESC
    LIMIT 10
    """, (username,))

    scores_data = cur.fetchall()

    scores = [s[0] for s in scores_data]
    totals = [s[1] for s in scores_data]

    percentages = [
        round((s/t)*100) if t > 0 else 0
        for s, t in zip(scores, totals)
    ]

    scores.reverse()
    percentages.reverse()

    cur.close()
    conn.close()

    level_up = session.pop('level_up', False)

    return render_template(
    'profile.html',
    username=username,
    xp=xp,
    rank=get_rank(xp),
    progress=get_progress(xp),  # ✅ NEW
    accuracy=accuracy,
    attempts=attempts,
    score=score,
    scores=scores,
    percentages=percentages,
    totals=totals,
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


@app.route('/ai_explain', methods=['POST'])
def ai_explain():
    try:
        data = request.get_json()

        index = data.get("index")
        user_answer = data.get("user_answer", "")

        questions = session.get("questions", [])

        if questions is None or index is None:
            return jsonify({"error": "Question Data Not Found"})

        if index >= len(questions):
            return jsonify({"error": "Invalid Question Index"})

        q = questions[index]

        explanation = generate_explanation(q, user_answer)

        return jsonify(explanation)

    except Exception as e:
        app.logger.error(f"AI Explain Error: {e}")
        return jsonify({"error": "Something Went Wrong"})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
