import os
import re
import random
from flask import Flask, render_template, request, session, jsonify

# =========================================================
# 🚀 FLASK APP SETUP
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

    elif "×" in question or "x" in question.lower():
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
# 📊 QUESTIONS DATABASE (SAMPLE)
# =========================================================
all_questions = [
    {"q":"What is 10% of ₹200?","options":["10","20","30","40"],"answer":"20","type":"quant","difficulty":"easy"},
    {"q":"Find the next number in the series: 2, 4, 6, 8, ?","options":["9","10","11","12"],"answer":"10","type":"logic","difficulty":"easy"},
    {"q":"Choose the correct word: He ___ playing.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy"},
    {"q":"A value increases from 100 to 200. What is the increase?","options":["50","100","150","200"],"answer":"100","type":"di","difficulty":"easy"},
]

# =========================================================
# 🔗 ROUTES
# =========================================================
@app.route("/")
def home():
    return render_template("index.html", questions=all_questions)

@app.route("/explanation", methods=["POST"])
def explanation():
    data = request.json
    question = data.get("question")
    answer = data.get("answer")
    qtype = data.get("type")
    explanation = generate_explanations(question, answer, qtype)
    return jsonify(explanation)

@app.route("/random-question")
def random_question():
    question = random.choice(all_questions)
    return jsonify(question)

# =========================================================
# 🚀 APP ENTRY
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
