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
import re

def generate_explanation(q, user_answer=None):
    question = q.get("q", "")
    correct = q.get("answer", "")
    qtype = q.get("type", "")
    subtype = q.get("subtype", "")

    # Extract numbers for calculation-based logic
    nums = list(map(float, re.findall(r'\d+\.?\d*', question)))

    why_wrong = ""
    if user_answer and str(user_answer).strip() != str(correct).strip():
        why_wrong = f"Your Answer: {user_answer}\nCorrect Answer: {correct}\nCheck Concept & Steps"

    level1, level2, level3 = correct, "", ""

    # ================= QUANT QUESTIONS =================
    if qtype == "quant":
        if subtype in ["percentage"]:
            if len(nums) >= 2:
                p, v = nums[0], nums[1]
                level2 = f"Percentage Formula: ({p}/100) × {v} = {(p/100)*v}"
                level3 = f"A Percentage Means A Part Out Of 100. So {p}% Of {v} Means We Take {p} Parts Out Of Every 100 And Apply To {v}, Giving {(p/100)*v}"
        
        elif subtype in ["average"]:
            if nums:
                avg = sum(nums)/len(nums)
                level2 = f"Average = Sum({nums}) / Count({len(nums)}) = {avg}"
                level3 = f"To Find Average, Add All Numbers Together Then Divide By How Many Numbers There Are. Here Sum={sum(nums)}, Count={len(nums)}, So Average={avg}"
        
        elif subtype in ["multiplication", "arithmetic"]:
            if len(nums) >= 2:
                level2 = f"Multiply {nums[0]} × {nums[1]} = {nums[0]*nums[1]}"
                level3 = f"Multiplication Means Adding {nums[0]} Together {int(nums[1])} Times. So {nums[0]} × {nums[1]} = {nums[0]*nums[1]}"
        
        elif subtype in ["division"]:
            if len(nums) >= 2:
                level2 = f"Divide {nums[0]} ÷ {nums[1]} = {nums[0]/nums[1]}"
                level3 = f"Division Means Splitting {nums[0]} Into {nums[1]} Equal Parts. Each Part Is {nums[0]/nums[1]}"
        
        elif subtype in ["square"]:
            if nums:
                level2 = f"{nums[0]}² = {nums[0]**2}"
                level3 = f"Square Means Multiply The Number By Itself. So {nums[0]} × {nums[0]} = {nums[0]**2}"
        
        elif subtype in ["cube"]:
            if nums:
                level2 = f"{nums[0]}³ = {nums[0]**3}"
                level3 = f"Cube Means Multiply The Number By Itself Twice More. So {nums[0]} × {nums[0]} × {nums[0]} = {nums[0]**3}"
        
        elif subtype in ["subtraction"]:
            if len(nums) >= 2:
                level2 = f"{nums[0]} - {nums[1]} = {nums[0]-nums[1]}"
                level3 = f"Subtraction Means Removing {nums[1]} From {nums[0]}, Resulting In {nums[0]-nums[1]}"
        
        elif subtype in ["interest", "simple_interest"]:
            if len(nums) >= 3:
                p, r, t = nums
                si = (p*r*t)/100
                level2 = f"SI = (Principal × Rate × Time)/100 = ({p}×{r}×{t})/100 = {si}"
                level3 = f"Simple Interest Means Paying Extra Money Based On Principal And Time. Formula: P×R×T /100, Here It Gives {si}"
        
        elif subtype in ["compound_interest"]:
            if len(nums) >= 3:
                p, r, t = nums
                ci = p*((1+r/100)**t -1)
                level2 = f"CI = P*((1+R/100)^T -1) = {ci}"
                level3 = f"Compound Interest Means Interest Is Added Each Year To Principal, So Next Year Interest Is On Bigger Amount. Computed Here As {ci}"
        
        elif subtype in ["ratio"]:
            if len(nums) >= 3:
                total = nums[2]
                a, b = nums[0], nums[1]
                smaller = (a/(a+b))*total
                level2 = f"Ratio {a}:{b} Sum={total} → Smaller Part = {smaller}"
                level3 = f"Total Is Split In Ratio {a}:{b}. Smaller Part = Total × (a/(a+b)) = {smaller}"
        
        elif subtype in ["hcf"]:
            from math import gcd
            if len(nums) >= 2:
                h = int(gcd(int(nums[0]), int(nums[1])))
                level2 = f"HCF of {int(nums[0])} and {int(nums[1])} = {h}"
                level3 = f"HCF Means Largest Number That Divides Both Numbers Exactly. Here It's {h}"
        
        elif subtype in ["lcm"]:
            from math import gcd
            if len(nums) >= 2:
                l = int(nums[0]*nums[1]/gcd(int(nums[0]), int(nums[1])))
                level2 = f"LCM of {int(nums[0])} and {int(nums[1])} = {l}"
                level3 = f"LCM Means Smallest Number Divisible By Both Numbers. Calculated As ({int(nums[0])}*{int(nums[1])})/GCD = {l}"
        
        elif subtype in ["root"]:
            if nums:
                level2 = f"√{nums[0]} = {nums[0]**0.5}"
                level3 = f"Square Root Means Number Which When Multiplied By Itself Gives Original. √{nums[0]} = {nums[0]**0.5}"

    # ================= LOGIC QUESTIONS =================
    elif qtype == "logic":
        if subtype == "series":
            level2 = f"Observe Pattern, Find Rule, Apply To Next Term = {correct}"
            level3 = f"In Series Questions, Look At Difference Or Multiplication Pattern Between Numbers. Then Apply The Same Rule To Find The Next Term. Answer Here Is {correct}"
        elif subtype == "odd_one":
            level2 = f"Identify Which Option Does Not Belong = {correct}"
            level3 = f"Look For The Word/Number That Breaks The Pattern Or Category. Answer = {correct}"
        elif subtype == "pattern":
            level2 = f"Observe Pattern/Formula In Numbers = {correct}"
            level3 = f"Patterns Are Special Rules Applied Across The Sequence. Follow The Rule Step By Step To Identify Missing Term. Answer = {correct}"
        elif subtype == "power":
            level2 = f"Find Pattern In Powers = {correct}"
            level3 = f"Each Number Is Raised To Certain Power To Get Next. Identify And Apply Rule. Answer = {correct}"
        elif subtype == "factorial":
            level2 = f"Compute Factorial Pattern = {correct}"
            level3 = f"Factorial Of N = Multiply All Numbers From 1 To N. Follow Sequence To Get Next Term. Answer = {correct}"

    # ================= VERBAL QUESTIONS =================
    elif qtype == "verbal":
        if subtype == "grammar":
            level2 = f"Use Correct Grammar Rule → {correct}"
            level3 = f"Understand Subject-Verb Agreement Or Tense. Fill The Blank Accordingly. Answer = {correct}"
        elif subtype == "synonym":
            level2 = f"Identify Word With Same Meaning → {correct}"
            level3 = f"Synonym Means Words With Similar Meaning. Look For Word That Matches Sense Of Question. Answer = {correct}"
        elif subtype == "antonym":
            level2 = f"Identify Word With Opposite Meaning → {correct}"
            level3 = f"Antonym Means Words With Opposite Meaning. Look For Word That Is Contrary In Sense. Answer = {correct}"
        elif subtype == "plural":
            level2 = f"Find Correct Plural Form → {correct}"
            level3 = f"Plural Means More Than One. Use Standard Rules Or Exceptions To Form Plural. Answer = {correct}"
        elif subtype == "spelling":
            level2 = f"Correct Spelling → {correct}"
            level3 = f"Check Standard English Spelling Rules Or Memory. Correct Spelling = {correct}"
        elif subtype == "article":
            level2 = f"Choose Correct Article → {correct}"
            level3 = f"Use 'a' Before Consonant Sounds And 'an' Before Vowel Sounds. Answer = {correct}"

    # ================= DEFAULT =================
    if not level2:
        level2 = "Apply Logical Steps To Solve"
    if not level3:
        level3 = "Break Down Question, Understand Concept, Solve Step By Step"

    return {
        "level1": level1,
        "level2": level2,
        "level3": level3,
        "level4": f"AI Explanation Placeholder For Button → Detailed Stepwise Explanation For Question: {question}",
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


@app.route('/profile')
def dashboard():

    if 'username' not in session:
        return redirect('/')

    username = session['username']

    conn = get_db_connection()
    cur = conn.cursor()

    # USER DATA
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

    # FAKE HISTORY (Optional Upgrade Later)
    scores = [score]  # You Can Later Store History In DB
    totals = [attempts]

    cur.close()
    conn.close()

    return render_template(
        'profile.html',
        username=username,
        xp=xp,
        rank=get_rank(xp),
        accuracy=accuracy,
        attempts=attempts,
        score=score,
        scores=scores,
        totals=totals
    )

@app.route('/leaderboard')
def leaderboard():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, xp, total_attempts
        FROM users
        ORDER BY xp DESC
        LIMIT 10
    """)

    users = cur.fetchall()

    # ADD RANK LABEL
    data = []
    for u in users:
        rank = get_rank(u[1])
        data.append((u[0], u[1], u[2], rank))

    cur.close()
    conn.close()

    return render_template("result.html",
    level_up=level_up,
    rank=new_rank
    )

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
