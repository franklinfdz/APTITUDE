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
all_questions = all_questions = [

# ================= EASY QUANT =================
{"q":"What is 10% of 150?","options":["10","15","20","25"],"answer":"15","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"What is 20% of 200?","options":["30","40","50","60"],"answer":"40","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"Find 25% of 80.","options":["10","15","20","25"],"answer":"20","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"What is 5 × 6?","options":["25","30","35","40"],"answer":"30","type":"quant","difficulty":"easy","subtype":"multiplication"},
{"q":"What is 81 ÷ 9?","options":["7","8","9","10"],"answer":"9","type":"quant","difficulty":"easy","subtype":"division"},
{"q":"Square of 6?","options":["30","36","42","48"],"answer":"36","type":"quant","difficulty":"easy","subtype":"square"},
{"q":"Cube of 2?","options":["6","8","10","12"],"answer":"8","type":"quant","difficulty":"easy","subtype":"cube"},
{"q":"Half of 120?","options":["50","60","70","80"],"answer":"60","type":"quant","difficulty":"easy","subtype":"division"},
{"q":"Average of 4 and 8?","options":["5","6","7","8"],"answer":"6","type":"quant","difficulty":"easy","subtype":"average"},
{"q":"100 - 45 = ?","options":["45","50","55","60"],"answer":"55","type":"quant","difficulty":"easy","subtype":"subtraction"},

# ================= EASY LOGIC =================
{"q":"Find next: 2, 4, 6, 8, ?","options":["9","10","11","12"],"answer":"10","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Find next: 5, 10, 15, 20, ?","options":["22","24","25","30"],"answer":"25","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Missing: 1, 3, 5, ?, 9","options":["6","7","8","10"],"answer":"7","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Dog, Cat, Cow, Car","options":["Dog","Cat","Cow","Car"],"answer":"Car","type":"logic","difficulty":"easy","subtype":"odd_one"},
{"q":"Next: 3, 6, 9, 12, ?","options":["14","15","16","18"],"answer":"15","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 10, 20, 30, ?","options":["35","40","45","50"],"answer":"40","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 7, 14, 21, ?","options":["24","28","30","35"],"answer":"28","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Apple, Banana, Mango, Potato","options":["Apple","Banana","Mango","Potato"],"answer":"Potato","type":"logic","difficulty":"easy","subtype":"odd_one"},
{"q":"Next: 1, 2, 3, 4, ?","options":["5","6","7","8"],"answer":"5","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 9, 18, 27, ?","options":["30","32","36","40"],"answer":"36","type":"logic","difficulty":"easy","subtype":"series"},

# ================= EASY VERBAL =================
{"q":"He ___ playing.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Synonym of Happy","options":["Sad","Joyful","Angry","Lazy"],"answer":"Joyful","type":"verbal","difficulty":"easy","subtype":"synonym"},
{"q":"Antonym of Big","options":["Large","Huge","Small","Wide"],"answer":"Small","type":"verbal","difficulty":"easy","subtype":"antonym"},
{"q":"She ___ a teacher.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Correct spelling","options":["Recieve","Receive","Recive","Receve"],"answer":"Receive","type":"verbal","difficulty":"easy","subtype":"spelling"},
{"q":"Plural of Book","options":["Book","Books","Bookes","Books"],"answer":"Books","type":"verbal","difficulty":"easy","subtype":"plural"},
{"q":"Synonym of Fast","options":["Slow","Quick","Late","Lazy"],"answer":"Quick","type":"verbal","difficulty":"easy","subtype":"synonym"},
{"q":"Antonym of Cold","options":["Hot","Cool","Warm","Freeze"],"answer":"Hot","type":"verbal","difficulty":"easy","subtype":"antonym"},
{"q":"We ___ friends.","options":["is","are","am","be"],"answer":"are","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Correct article: ___ apple","options":["a","an","the","no"],"answer":"an","type":"verbal","difficulty":"easy","subtype":"article"},

# ================= MEDIUM QUANT =================
{"q":"Simple interest on ₹1000 at 5% for 2 years?","options":["100","150","200","250"],"answer":"100","type":"quant","difficulty":"medium","subtype":"interest"},
{"q":"A number increased by 20% becomes 120. Find original.","options":["80","90","100","110"],"answer":"100","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"Average of 10,20,30?","options":["15","20","25","30"],"answer":"20","type":"quant","difficulty":"medium","subtype":"average"},
{"q":"Find LCM of 6 and 8","options":["12","24","36","48"],"answer":"24","type":"quant","difficulty":"medium","subtype":"lcm"},
{"q":"Find HCF of 12 and 18","options":["3","6","9","12"],"answer":"6","type":"quant","difficulty":"medium","subtype":"hcf"},
{"q":"Speed: 120 km in 4 hr?","options":["20","25","30","35"],"answer":"30","type":"quant","difficulty":"medium","subtype":"speed"},
{"q":"15 × 12 = ?","options":["160","170","180","190"],"answer":"180","type":"quant","difficulty":"medium","subtype":"multiplication"},
{"q":"Square of 15?","options":["200","225","250","275"],"answer":"225","type":"quant","difficulty":"medium","subtype":"square"},
{"q":"20% of 250?","options":["40","45","50","55"],"answer":"50","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"Ratio 2:3 sum 50 find smaller","options":["15","20","25","30"],"answer":"20","type":"quant","difficulty":"medium","subtype":"ratio"},

# ================= MEDIUM LOGIC =================
{"q":"Next: 2, 6, 18, 54, ?","options":["108","120","162","180"],"answer":"162","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Missing: 4, 9, 16, ?, 36","options":["20","24","25","30"],"answer":"25","type":"logic","difficulty":"medium","subtype":"square"},
{"q":"Odd one: Circle, Square, Triangle, Sphere","options":["Circle","Square","Triangle","Sphere"],"answer":"Sphere","type":"logic","difficulty":"medium","subtype":"odd_one"},
{"q":"Next: 100, 50, 25, ?","options":["10","12.5","15","20"],"answer":"12.5","type":"logic","difficulty":"medium","subtype":"division"},
{"q":"Next: 1, 4, 10, 22, ?","options":["42","44","46","48"],"answer":"46","type":"logic","difficulty":"medium","subtype":"pattern"},

# ================= MEDIUM VERBAL =================
{"q":"They ___ finished.","options":["has","have","had","having"],"answer":"have","type":"verbal","difficulty":"medium","subtype":"grammar"},
{"q":"Synonym of Rapid","options":["Slow","Quick","Late","Soft"],"answer":"Quick","type":"verbal","difficulty":"medium","subtype":"synonym"},
{"q":"Antonym of Expand","options":["Grow","Increase","Shrink","Extend"],"answer":"Shrink","type":"verbal","difficulty":"medium","subtype":"antonym"},
{"q":"Plural of Analysis","options":["Analysises","Analyses","Analysis","Analys"],"answer":"Analyses","type":"verbal","difficulty":"medium","subtype":"plural"},
{"q":"Correct spelling","options":["Accomodate","Acommodate","Accommodate","Acomodate"],"answer":"Accommodate","type":"verbal","difficulty":"medium","subtype":"spelling"},

# ================= HARD QUANT =================
{"q":"Compound interest on ₹1000 at 10% for 2 years?","options":["200","210","220","250"],"answer":"210","type":"quant","difficulty":"hard","subtype":"compound_interest"},
{"q":"Square root of 1764?","options":["40","42","44","46"],"answer":"42","type":"quant","difficulty":"hard","subtype":"root"},
{"q":"If 30% = 90 find number","options":["200","250","300","350"],"answer":"300","type":"quant","difficulty":"hard","subtype":"percentage"},
{"q":"HCF=15 LCM=225 one=45 find other","options":["50","60","75","90"],"answer":"75","type":"quant","difficulty":"hard","subtype":"hcf_lcm"},
{"q":"A sum doubles in 4 years find rate","options":["12.5%","15%","18%","25%"],"answer":"25%","type":"quant","difficulty":"hard","subtype":"interest"},

# ================= HARD LOGIC =================
{"q":"Next: 2, 5, 10, 17, 26, ?","options":["35","36","37","38"],"answer":"37","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Missing: 3, 8, 15, 24, 35, ?","options":["46","48","49","50"],"answer":"48","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Next: 1, 3, 7, 15, 31, ?","options":["55","60","63","65"],"answer":"63","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Next: 4, 16, 64, 256, ?","options":["512","768","1024","2048"],"answer":"1024","type":"logic","difficulty":"hard","subtype":"power"},
{"q":"Next: 1, 2, 6, 24, 120, ?","options":["720","5040","7200","3600"],"answer":"720","type":"logic","difficulty":"hard","subtype":"factorial"},

# ================= HARD VERBAL =================
{"q":"Synonym of Benevolent","options":["Kind","Harsh","Rude","Cold"],"answer":"Kind","type":"verbal","difficulty":"hard","subtype":"synonym"},
{"q":"Antonym of Scarce","options":["Rare","Plenty","Less","Small"],"answer":"Plenty","type":"verbal","difficulty":"hard","subtype":"antonym"},
{"q":"Hardly had she entered ___ bell rang","options":["than","when","then","while"],"answer":"when","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Plural of Thesis","options":["Thesises","Theses","Thesis","Theis"],"answer":"Theses","type":"verbal","difficulty":"hard","subtype":"plural"},
{"q":"Correct spelling","options":["Pronounciation","Pronunciation","Pronuncation","Prononciation"],"answer":"Pronunciation","type":"verbal","difficulty":"hard","subtype":"spelling"},
    
# =========================================================
# 🟢 EASY QUANT (MORE)
# =========================================================
{"q":"What is 30% of 200?","options":["40","50","60","70"],"answer":"60","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"What is 40% of 150?","options":["50","60","70","80"],"answer":"60","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"Find 10% of 500.","options":["40","50","60","70"],"answer":"50","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"What is 9 × 7?","options":["56","63","72","81"],"answer":"63","type":"quant","difficulty":"easy","subtype":"multiplication"},
{"q":"144 ÷ 12 = ?","options":["10","11","12","13"],"answer":"12","type":"quant","difficulty":"easy","subtype":"division"},
{"q":"Square of 8?","options":["56","64","72","80"],"answer":"64","type":"quant","difficulty":"easy","subtype":"square"},
{"q":"Cube of 5?","options":["100","125","150","175"],"answer":"125","type":"quant","difficulty":"easy","subtype":"cube"},
{"q":"Half of 200?","options":["80","90","100","110"],"answer":"100","type":"quant","difficulty":"easy","subtype":"division"},
{"q":"Average of 6 and 10?","options":["6","7","8","9"],"answer":"8","type":"quant","difficulty":"easy","subtype":"average"},
{"q":"250 - 100 = ?","options":["100","120","150","170"],"answer":"150","type":"quant","difficulty":"easy","subtype":"subtraction"},

# =========================================================
# 🟢 EASY LOGIC (MORE)
# =========================================================
{"q":"Find next: 4, 8, 12, 16, ?","options":["18","20","22","24"],"answer":"20","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Find next: 6, 12, 18, 24, ?","options":["28","30","32","34"],"answer":"30","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Missing: 2, 4, ?, 8","options":["5","6","7","8"],"answer":"6","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Pen, Pencil, Book, Banana","options":["Pen","Pencil","Book","Banana"],"answer":"Banana","type":"logic","difficulty":"easy","subtype":"odd_one"},
{"q":"Next: 11, 22, 33, ?","options":["40","44","45","50"],"answer":"44","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 2, 3, 4, 5, ?","options":["6","7","8","9"],"answer":"6","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 5, 15, 25, ?","options":["30","35","40","45"],"answer":"35","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Rose, Lily, Lotus, Table","options":["Rose","Lily","Lotus","Table"],"answer":"Table","type":"logic","difficulty":"easy","subtype":"odd_one"},
{"q":"Next: 100, 200, 300, ?","options":["350","400","450","500"],"answer":"400","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Next: 8, 16, 24, ?","options":["30","32","34","36"],"answer":"32","type":"logic","difficulty":"easy","subtype":"series"},

# =========================================================
# 🟢 EASY VERBAL (MORE)
# =========================================================
{"q":"He ___ my friend.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Synonym of Small","options":["Tiny","Huge","Big","Large"],"answer":"Tiny","type":"verbal","difficulty":"easy","subtype":"synonym"},
{"q":"Antonym of Up","options":["Down","Top","Above","Over"],"answer":"Down","type":"verbal","difficulty":"easy","subtype":"antonym"},
{"q":"I ___ a student.","options":["is","are","am","be"],"answer":"am","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Correct spelling","options":["Enviroment","Environment","Environmnt","Enviroment"],"answer":"Environment","type":"verbal","difficulty":"easy","subtype":"spelling"},
{"q":"Plural of Car","options":["Car","Cars","Cares","Carses"],"answer":"Cars","type":"verbal","difficulty":"easy","subtype":"plural"},
{"q":"Synonym of Easy","options":["Hard","Simple","Tough","Complex"],"answer":"Simple","type":"verbal","difficulty":"easy","subtype":"synonym"},
{"q":"Antonym of Near","options":["Far","Close","Next","Beside"],"answer":"Far","type":"verbal","difficulty":"easy","subtype":"antonym"},
{"q":"They ___ playing.","options":["is","are","am","be"],"answer":"are","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Correct article: ___ umbrella","options":["a","an","the","no"],"answer":"an","type":"verbal","difficulty":"easy","subtype":"article"},

# =========================================================
# 🟡 MEDIUM QUANT (MORE)
# =========================================================
{"q":"Find SI on ₹2000 at 10% for 2 years","options":["200","300","400","500"],"answer":"400","type":"quant","difficulty":"medium","subtype":"interest"},
{"q":"A number increased by 50% becomes 150","options":["80","90","100","110"],"answer":"100","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"Average of 20,30,40","options":["25","30","35","40"],"answer":"30","type":"quant","difficulty":"medium","subtype":"average"},
{"q":"LCM of 10 and 15","options":["20","25","30","35"],"answer":"30","type":"quant","difficulty":"medium","subtype":"lcm"},
{"q":"HCF of 18 and 24","options":["3","6","9","12"],"answer":"6","type":"quant","difficulty":"medium","subtype":"hcf"},
{"q":"Speed: 150 km in 3 hr","options":["40","45","50","55"],"answer":"50","type":"quant","difficulty":"medium","subtype":"speed"},
{"q":"12 × 14 = ?","options":["150","160","168","180"],"answer":"168","type":"quant","difficulty":"medium","subtype":"multiplication"},
{"q":"Square of 18","options":["300","324","350","360"],"answer":"324","type":"quant","difficulty":"medium","subtype":"square"},
{"q":"25% of 400","options":["80","90","100","120"],"answer":"100","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"Ratio 3:5 sum 80 find smaller","options":["20","25","30","35"],"answer":"30","type":"quant","difficulty":"medium","subtype":"ratio"},

# =========================================================
# 🟡 MEDIUM LOGIC (MORE)
# =========================================================
{"q":"Next: 3, 9, 27, ?","options":["54","72","81","90"],"answer":"81","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Missing: 5, 10, 20, ?, 80","options":["30","35","40","50"],"answer":"40","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Odd one: Apple, Mango, Banana, Carrot","options":["Apple","Mango","Banana","Carrot"],"answer":"Carrot","type":"logic","difficulty":"medium","subtype":"odd_one"},
{"q":"Next: 1, 4, 9, 16, ?","options":["20","24","25","30"],"answer":"25","type":"logic","difficulty":"medium","subtype":"square"},
{"q":"Next: 100, 80, 60, ?","options":["30","40","50","20"],"answer":"40","type":"logic","difficulty":"medium","subtype":"series"},

# =========================================================
# 🟡 MEDIUM VERBAL (MORE)
# =========================================================
{"q":"She ___ finished work.","options":["has","have","had","having"],"answer":"has","type":"verbal","difficulty":"medium","subtype":"grammar"},
{"q":"Synonym of Begin","options":["Start","End","Stop","Pause"],"answer":"Start","type":"verbal","difficulty":"medium","subtype":"synonym"},
{"q":"Antonym of Increase","options":["Raise","Grow","Decrease","Expand"],"answer":"Decrease","type":"verbal","difficulty":"medium","subtype":"antonym"},
{"q":"Plural of Mouse","options":["Mouses","Mice","Mouse","Mices"],"answer":"Mice","type":"verbal","difficulty":"medium","subtype":"plural"},
{"q":"Correct spelling","options":["Seperate","Separate","Seperete","Separete"],"answer":"Separate","type":"verbal","difficulty":"medium","subtype":"spelling"},

# =========================================================
# 🔴 HARD QUANT (MORE)
# =========================================================
{"q":"CI on ₹2000 at 5% for 2 years","options":["200","205","210","215"],"answer":"205","type":"quant","difficulty":"hard","subtype":"compound_interest"},
{"q":"√2025 = ?","options":["40","42","45","48"],"answer":"45","type":"quant","difficulty":"hard","subtype":"root"},
{"q":"If 20% = 80 find number","options":["300","350","400","450"],"answer":"400","type":"quant","difficulty":"hard","subtype":"percentage"},
{"q":"LCM=180 HCF=6 one=30 find other","options":["36","40","45","50"],"answer":"36","type":"quant","difficulty":"hard","subtype":"hcf_lcm"},
{"q":"Triples in 5 years rate?","options":["10%","15%","20%","25%"],"answer":"20%","type":"quant","difficulty":"hard","subtype":"interest"},

# =========================================================
# 🔴 HARD LOGIC (MORE)
# =========================================================
{"q":"Next: 5, 11, 23, 47, ?","options":["90","94","95","96"],"answer":"95","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Missing: 7, 10, 16, 28, 52, ?","options":["100","104","108","112"],"answer":"100","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Next: 2, 7, 26, 101, ?","options":["404","405","406","407"],"answer":"406","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Next: 9, 27, 81, ?","options":["162","243","324","400"],"answer":"243","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Next: 6, 24, 60, 120, ?","options":["180","210","240","300"],"answer":"210","type":"logic","difficulty":"hard","subtype":"pattern"},

# =========================================================
# 🔴 HARD VERBAL (MORE)
# =========================================================
{"q":"Synonym of Resilient","options":["Flexible","Weak","Fragile","Rigid"],"answer":"Flexible","type":"verbal","difficulty":"hard","subtype":"synonym"},
{"q":"Antonym of Explicit","options":["Clear","Hidden","Obvious","Direct"],"answer":"Hidden","type":"verbal","difficulty":"hard","subtype":"antonym"},
{"q":"She had ___ finished before he came","options":["already","yet","still","ever"],"answer":"already","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Each of the boys ___ present","options":["is","are","were","be"],"answer":"is","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Plural of Phenomenon","options":["Phenomenons","Phenomena","Phenomenas","Phenomenon"],"answer":"Phenomena","type":"verbal","difficulty":"hard","subtype":"plural"},
    

# ================= EASY QUANT =================
{"q":"What is 5% of 400?","options":["10","15","20","25"],"answer":"20","type":"quant","difficulty":"easy","subtype":"percentage"},
{"q":"What is 8 × 7?","options":["54","56","58","60"],"answer":"56","type":"quant","difficulty":"easy","subtype":"arithmetic"},
{"q":"What is 90 ÷ 9?","options":["8","9","10","11"],"answer":"10","type":"quant","difficulty":"easy","subtype":"division"},
{"q":"Find the square of 6.","options":["30","32","34","36"],"answer":"36","type":"quant","difficulty":"easy","subtype":"square"},
{"q":"What is 25% of 80?","options":["10","15","20","25"],"answer":"20","type":"quant","difficulty":"easy","subtype":"percentage"},

# ================= EASY LOGIC =================
{"q":"Find next: 3, 6, 9, ?","options":["10","11","12","13"],"answer":"12","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Dog, Cat, Tiger, Car","options":["Dog","Cat","Tiger","Car"],"answer":"Car","type":"logic","difficulty":"easy","subtype":"odd_one"},
{"q":"Find next: 2, 4, 8, ?","options":["10","12","14","16"],"answer":"16","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Missing: 5, 10, ?, 20","options":["12","14","15","16"],"answer":"15","type":"logic","difficulty":"easy","subtype":"series"},
{"q":"Odd one: Apple, Mango, Chair, Banana","options":["Apple","Mango","Chair","Banana"],"answer":"Chair","type":"logic","difficulty":"easy","subtype":"odd_one"},

# ================= EASY VERBAL =================
{"q":"Fill: He ___ reading.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy","subtype":"grammar"},
{"q":"Synonym of 'Small'","options":["Big","Tiny","Huge","Tall"],"answer":"Tiny","type":"verbal","difficulty":"easy","subtype":"synonym"},
{"q":"Antonym of 'Dark'","options":["Light","Black","Dim","Night"],"answer":"Light","type":"verbal","difficulty":"easy","subtype":"antonym"},
{"q":"Plural of 'Box'","options":["Boxs","Boxes","Boxes","Box"],"answer":"Boxes","type":"verbal","difficulty":"easy","subtype":"plural"},
{"q":"Correct spelling","options":["Enviroment","Environment","Enviornment","Envirnment"],"answer":"Environment","type":"verbal","difficulty":"easy","subtype":"spelling"},

# ================= MEDIUM QUANT =================
{"q":"What is 15% of 200?","options":["20","25","30","35"],"answer":"30","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"Find average of 5,10,15,20","options":["10","12.5","15","17.5"],"answer":"12.5","type":"quant","difficulty":"medium","subtype":"average"},
{"q":"If 3 pens cost ₹30, cost of 10 pens?","options":["90","100","110","120"],"answer":"100","type":"quant","difficulty":"medium","subtype":"ratio"},
{"q":"Speed = 60 km/h, time = 2h. Distance?","options":["100","110","120","130"],"answer":"120","type":"quant","difficulty":"medium","subtype":"speed"},
{"q":"Find SI on ₹1000 at 10% for 2 years","options":["100","150","200","250"],"answer":"200","type":"quant","difficulty":"medium","subtype":"interest"},

# ================= MEDIUM LOGIC =================
{"q":"Find next: 4, 9, 16, 25, ?","options":["30","35","36","40"],"answer":"36","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Missing: 2, 6, 18, ?, 162","options":["36","54","72","90"],"answer":"54","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Odd one: 2, 3, 5, 9, 11","options":["2","3","5","9"],"answer":"9","type":"logic","difficulty":"medium","subtype":"odd_one"},
{"q":"Find next: 1, 1, 2, 3, 5, ?","options":["6","7","8","9"],"answer":"8","type":"logic","difficulty":"medium","subtype":"series"},
{"q":"Find next: 100, 90, 80, ?","options":["60","65","70","75"],"answer":"70","type":"logic","difficulty":"medium","subtype":"series"},

# ================= MEDIUM VERBAL =================
{"q":"Fill: They ___ finished work.","options":["has","have","had","having"],"answer":"have","type":"verbal","difficulty":"medium","subtype":"grammar"},
{"q":"Synonym of 'Quick'","options":["Slow","Fast","Late","Soft"],"answer":"Fast","type":"verbal","difficulty":"medium","subtype":"synonym"},
{"q":"Antonym of 'Strong'","options":["Powerful","Weak","Solid","Hard"],"answer":"Weak","type":"verbal","difficulty":"medium","subtype":"antonym"},
{"q":"Plural of 'Crisis'","options":["Crisises","Crises","Crisis","Crise"],"answer":"Crises","type":"verbal","difficulty":"medium","subtype":"plural"},
{"q":"Correct spelling","options":["Occured","Occurred","Ocurred","Occur"],"answer":"Occurred","type":"verbal","difficulty":"medium","subtype":"spelling"},

# ================= HARD QUANT =================
{"q":"Find CI on ₹1000 at 10% for 2 years","options":["200","210","220","230"],"answer":"210","type":"quant","difficulty":"hard","subtype":"interest"},
{"q":"If 40% of x = 80, find x","options":["150","180","200","220"],"answer":"200","type":"quant","difficulty":"hard","subtype":"percentage"},
{"q":"A can do work in 10 days, B in 15. Together?","options":["4","5","6","7"],"answer":"6","type":"quant","difficulty":"hard","subtype":"time_work"},
{"q":"Find square root of 2025","options":["40","42","45","50"],"answer":"45","type":"quant","difficulty":"hard","subtype":"root"},
{"q":"Train speed 54 km/h, distance 300m time?","options":["15","20","25","30"],"answer":"20","type":"quant","difficulty":"hard","subtype":"speed"},

# ================= HARD LOGIC =================
{"q":"Find next: 2, 6, 24, 120, ?","options":["600","620","720","840"],"answer":"720","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Missing: 5, 11, 23, 47, ?","options":["90","91","93","95"],"answer":"95","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Find next: 3, 9, 27, 81, ?","options":["162","243","324","400"],"answer":"243","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Odd one: Cube, Sphere, Circle, Cylinder","options":["Cube","Sphere","Circle","Cylinder"],"answer":"Circle","type":"logic","difficulty":"hard","subtype":"odd_one"},
{"q":"Find next: 7, 14, 28, 56, ?","options":["84","96","112","120"],"answer":"112","type":"logic","difficulty":"hard","subtype":"series"},

# ================= HARD VERBAL =================
{"q":"Fill: Each student ___ responsible.","options":["is","are","were","be"],"answer":"is","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Synonym of 'Vivid'","options":["Clear","Dull","Dark","Blur"],"answer":"Clear","type":"verbal","difficulty":"hard","subtype":"synonym"},
{"q":"Antonym of 'Scarce'","options":["Rare","Less","Plenty","Few"],"answer":"Plenty","type":"verbal","difficulty":"hard","subtype":"antonym"},
{"q":"Plural of 'Phenomenon'","options":["Phenomenons","Phenomena","Phenomenas","Phenomen"],"answer":"Phenomena","type":"verbal","difficulty":"hard","subtype":"plural"},
{"q":"Correct spelling","options":["Conscious","Concious","Conscous","Concius"],"answer":"Conscious","type":"verbal","difficulty":"hard","subtype":"spelling"},


# ================= TRICKY QUANT =================
{"q":"If 20% of a number is 50, what is 40% of the same number?","options":["80","90","100","120"],"answer":"100","type":"quant","difficulty":"medium","subtype":"percentage"},
{"q":"A number is increased by 25% and then decreased by 20%. Final change?","options":["No change","5% increase","5% decrease","10% increase"],"answer":"No change","type":"quant","difficulty":"hard","subtype":"percentage"},
{"q":"If selling price = cost price, profit %?","options":["0%","10%","Loss","Cannot determine"],"answer":"0%","type":"quant","difficulty":"easy","subtype":"profit_loss"},
{"q":"A man buys at ₹100 and sells at ₹120. Profit %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"quant","difficulty":"easy","subtype":"profit_loss"},
{"q":"A train travels 60 km in 1 hour 30 minutes. Speed?","options":["30 km/h","40 km/h","45 km/h","50 km/h"],"answer":"40 km/h","type":"quant","difficulty":"medium","subtype":"speed"},

# ================= ADVANCED LOGIC =================
{"q":"Find next: 2, 3, 5, 9, 17, ?","options":["25","31","33","34"],"answer":"33","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Find next: 1, 2, 6, 24, 120, ?","options":["600","720","840","960"],"answer":"720","type":"logic","difficulty":"hard","subtype":"factorial"},
{"q":"Find missing: 4, 6, 9, 13, ?, 24","options":["16","17","18","19"],"answer":"18","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Find next: 10, 20, 30, 50, 80, ?","options":["100","110","120","130"],"answer":"130","type":"logic","difficulty":"hard","subtype":"series"},
{"q":"Find odd: 121, 144, 169, 196, 210","options":["121","144","169","210"],"answer":"210","type":"logic","difficulty":"medium","subtype":"odd_one"},

# ================= PUZZLE BASED =================
{"q":"If ALL = 36, BAT = 39, CAT = ?","options":["40","41","42","43"],"answer":"42","type":"logic","difficulty":"hard","subtype":"coding"},
{"q":"If 2+3=13, 3+4=25, then 4+5=?","options":["35","41","45","50"],"answer":"41","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Find next: A, C, F, J, O, ?","options":["S","T","U","V"],"answer":"U","type":"logic","difficulty":"hard","subtype":"alphabet"},
{"q":"If MON = 39, SUN = 54, then TUE = ?","options":["40","45","50","55"],"answer":"50","type":"logic","difficulty":"hard","subtype":"coding"},
{"q":"Find next: Z, X, U, Q, ?","options":["M","N","O","P"],"answer":"M","type":"logic","difficulty":"hard","subtype":"alphabet"},

# ================= INTERVIEW VERBAL =================
{"q":"Choose correct: He insisted that she ___ present.","options":["is","was","be","being"],"answer":"be","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Synonym of 'Meticulous'","options":["Careless","Detailed","Quick","Lazy"],"answer":"Detailed","type":"verbal","difficulty":"hard","subtype":"synonym"},
{"q":"Antonym of 'Abundant'","options":["Plenty","Scarce","Huge","Large"],"answer":"Scarce","type":"verbal","difficulty":"hard","subtype":"antonym"},
{"q":"Choose correct: No sooner had he arrived ___ it started raining.","options":["than","when","then","while"],"answer":"than","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Correct spelling","options":["Entreprenuer","Entrepreneur","Entreprenaur","Enterpreneur"],"answer":"Entrepreneur","type":"verbal","difficulty":"hard","subtype":"spelling"},

# ================= MIXED DI =================
{"q":"A company profit increased from ₹5000 to ₹6500. % increase?","options":["20%","25%","30%","35%"],"answer":"30%","type":"di","difficulty":"medium","subtype":"percentage"},
{"q":"Population grows from 10000 to 12100. % growth?","options":["10%","15%","20%","21%"],"answer":"21%","type":"di","difficulty":"medium","subtype":"percentage"},
{"q":"A product costs ₹400, sold at ₹480. Profit %?","options":["15%","20%","25%","30%"],"answer":"20%","type":"di","difficulty":"medium","subtype":"profit_loss"},
{"q":"Loss ₹100 on cost ₹500. Loss %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy","subtype":"profit_loss"},
{"q":"Increase 200 → 260. % increase?","options":["20%","25%","30%","35%"],"answer":"30%","type":"di","difficulty":"easy","subtype":"percentage"},

# ================= BRAIN TWISTERS =================
{"q":"A father is 3 times his son's age. After 10 years, he is 2 times. Current son's age?","options":["10","15","20","25"],"answer":"10","type":"quant","difficulty":"hard","subtype":"age"},
{"q":"If 5 machines make 5 items in 5 minutes, 100 machines make 100 items in?","options":["5","10","50","100"],"answer":"5","type":"quant","difficulty":"hard","subtype":"logic_math"},
{"q":"A clock shows 3:15. Angle between hands?","options":["0°","7.5°","15°","30°"],"answer":"7.5°","type":"quant","difficulty":"hard","subtype":"clock"},
{"q":"Find remainder: 7^2 ÷ 5","options":["2","3","4","1"],"answer":"4","type":"quant","difficulty":"medium","subtype":"modulus"},
{"q":"Find next: 1, 11, 21, 1211, 111221, ?","options":["312211","1112211","1211","2121"],"answer":"312211","type":"logic","difficulty":"hard","subtype":"series"},


# ================= ULTRA QUANT =================
{"q":"A number is increased by 20% and then decreased by 20%. Final result?","options":["Same","4% increase","4% decrease","No change"],"answer":"4% decrease","type":"quant","difficulty":"hard","subtype":"percentage_trap"},
{"q":"If 12 men can do a work in 10 days, how many days will 15 men take?","options":["6","7","8","9"],"answer":"8","type":"quant","difficulty":"hard","subtype":"time_work"},
{"q":"A sum becomes ₹1200 in 2 years and ₹1400 in 4 years. Find principal.","options":["800","900","1000","1100"],"answer":"1000","type":"quant","difficulty":"hard","subtype":"interest"},
{"q":"If cost price increases by 25% but selling price remains same, profit?","options":["Increase","Decrease","Same","Loss"],"answer":"Decrease","type":"quant","difficulty":"hard","subtype":"profit_logic"},
{"q":"Find remainder when 17^3 is divided by 5","options":["1","2","3","4"],"answer":"3","type":"quant","difficulty":"hard","subtype":"modulus"},

# ================= MULTI-STEP LOGIC =================
{"q":"Find next: 2, 6, 7, 21, 22, 66, ?","options":["67","68","69","70"],"answer":"67","type":"logic","difficulty":"hard","subtype":"pattern_mix"},
{"q":"Find missing: 3, 9, 27, ?, 243","options":["54","72","81","90"],"answer":"81","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Find next: 1, 4, 10, 22, 46, ?","options":["90","92","94","96"],"answer":"94","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"Find odd: 3, 5, 11, 14, 17","options":["3","5","11","14"],"answer":"14","type":"logic","difficulty":"hard","subtype":"odd_one"},
{"q":"Find next: 5, 10, 20, 40, 80, ?","options":["120","140","150","160"],"answer":"160","type":"logic","difficulty":"medium","subtype":"series"},

# ================= CODING + ALPHABET =================
{"q":"If CAT = 24, DOG = 26, then BAT = ?","options":["20","21","22","23"],"answer":"22","type":"logic","difficulty":"hard","subtype":"coding"},
{"q":"If A=1, B=2... what is value of 'ACE'?","options":["9","10","11","12"],"answer":"9","type":"logic","difficulty":"medium","subtype":"alphabet"},
{"q":"Find next: B, E, I, N, T, ?","options":["Z","Y","X","W"],"answer":"Z","type":"logic","difficulty":"hard","subtype":"alphabet"},
{"q":"If SKY = 55, SUN = 54, then SEA = ?","options":["25","26","27","28"],"answer":"25","type":"logic","difficulty":"hard","subtype":"coding"},
{"q":"Find next: A, D, H, M, S, ?","options":["X","Y","Z","W"],"answer":"Z","type":"logic","difficulty":"hard","subtype":"alphabet"},

# ================= REAL INTERVIEW VERBAL =================
{"q":"Choose correct: Hardly ___ he reached when it started raining.","options":["had","has","have","did"],"answer":"had","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Synonym of 'Pragmatic'","options":["Idealistic","Practical","Dreamy","Lazy"],"answer":"Practical","type":"verbal","difficulty":"hard","subtype":"synonym"},
{"q":"Antonym of 'Opaque'","options":["Dark","Transparent","Solid","Heavy"],"answer":"Transparent","type":"verbal","difficulty":"hard","subtype":"antonym"},
{"q":"Choose correct: She is one of those students who ___ always punctual.","options":["is","are","was","be"],"answer":"are","type":"verbal","difficulty":"hard","subtype":"grammar"},
{"q":"Correct spelling","options":["Millenium","Millennium","Milleniume","Mileniumm"],"answer":"Millennium","type":"verbal","difficulty":"hard","subtype":"spelling"},

# ================= CASE-BASED DI =================
{"q":"Revenue increased from ₹2000 to ₹2600. % increase?","options":["20%","25%","30%","35%"],"answer":"30%","type":"di","difficulty":"medium","subtype":"percentage"},
{"q":"Expenses decreased from ₹1500 to ₹1200. % decrease?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"medium","subtype":"percentage"},
{"q":"Profit = ₹500, Cost = ₹2000. Profit %?","options":["20%","25%","30%","35%"],"answer":"25%","type":"di","difficulty":"medium","subtype":"profit_loss"},
{"q":"Population grew 10% annually for 2 years. Net growth?","options":["20%","21%","22%","25%"],"answer":"21%","type":"di","difficulty":"hard","subtype":"compound"},
{"q":"Value drops from ₹1000 to ₹810. % decrease?","options":["10%","15%","19%","20%"],"answer":"19%","type":"di","difficulty":"hard","subtype":"percentage"},

# ================= ELITE BRAIN TWISTERS =================
{"q":"A man walks 10m south, then 10m east, then 10m north. How far from start?","options":["0","10","20","30"],"answer":"10","type":"logic","difficulty":"medium","subtype":"direction"},
{"q":"If 1=5, 2=25, 3=325, 4=4325, then 5=?","options":["54325","50000","43250","None"],"answer":"54325","type":"logic","difficulty":"hard","subtype":"pattern"},
{"q":"A clock shows 6:00. Angle between hands?","options":["0°","90°","180°","360°"],"answer":"180°","type":"quant","difficulty":"easy","subtype":"clock"},
{"q":"If 3 cats catch 3 rats in 3 minutes, 100 cats catch 100 rats in?","options":["3","10","50","100"],"answer":"3","type":"quant","difficulty":"hard","subtype":"logic_math"},
{"q":"Find next: 1, 2, 4, 7, 11, 16, ?","options":["20","21","22","23"],"answer":"22","type":"logic","difficulty":"medium","subtype":"series"}

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
