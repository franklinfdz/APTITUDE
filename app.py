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
all_questions =  [

{"q":"What is 10% of ₹200?","options":["10","20","30","40"],"answer":"20","type":"quant","difficulty":"easy"},
{"q":"What is 25% of 100?","options":["20","25","30","40"],"answer":"25","type":"quant","difficulty":"easy"},
{"q":"Find the sum of 20 and 30.","options":["40","50","60","70"],"answer":"50","type":"quant","difficulty":"easy"},
{"q":"What is the square of 5?","options":["10","15","20","25"],"answer":"25","type":"quant","difficulty":"easy"},
{"q":"What is 100 divided by 10?","options":["5","10","15","20"],"answer":"10","type":"quant","difficulty":"easy"},

{"q":"If a pen costs ₹10, what is the cost of 5 pens?","options":["40","50","60","70"],"answer":"50","type":"quant","difficulty":"easy"},
{"q":"What is 50% of ₹300?","options":["100","150","200","250"],"answer":"150","type":"quant","difficulty":"easy"},
{"q":"Find the value of 7 × 8.","options":["54","56","58","60"],"answer":"56","type":"quant","difficulty":"easy"},
{"q":"What is 81 ÷ 9?","options":["7","8","9","10"],"answer":"9","type":"quant","difficulty":"easy"},
{"q":"Find the cube of 3.","options":["9","18","27","36"],"answer":"27","type":"quant","difficulty":"easy"},

{"q":"What is the average of 10 and 20?","options":["10","15","20","25"],"answer":"15","type":"quant","difficulty":"easy"},
{"q":"What is 15% of 200?","options":["20","25","30","35"],"answer":"30","type":"quant","difficulty":"easy"},
{"q":"What is 200 - 75?","options":["100","110","125","150"],"answer":"125","type":"quant","difficulty":"easy"},
{"q":"If 1 item costs ₹50, what is the cost of 2 items?","options":["80","90","100","120"],"answer":"100","type":"quant","difficulty":"easy"},
{"q":"Find the sum of first 5 natural numbers.","options":["10","15","20","25"],"answer":"15","type":"quant","difficulty":"easy"},

{"q":"What is 12 × 12?","options":["124","144","154","164"],"answer":"144","type":"quant","difficulty":"easy"},
{"q":"What is half of 80?","options":["30","35","40","45"],"answer":"40","type":"quant","difficulty":"easy"},
{"q":"What is 5 squared?","options":["20","25","30","35"],"answer":"25","type":"quant","difficulty":"easy"},
{"q":"Find 30% of 300.","options":["60","70","80","90"],"answer":"90","type":"quant","difficulty":"easy"},
{"q":"What is 9 × 9?","options":["72","81","90","99"],"answer":"81","type":"quant","difficulty":"easy"},

{"q":"What is 1000 ÷ 100?","options":["5","10","15","20"],"answer":"10","type":"quant","difficulty":"easy"},
{"q":"Find the value of 6 × 7.","options":["40","42","44","48"],"answer":"42","type":"quant","difficulty":"easy"},
{"q":"What is 45 + 55?","options":["90","95","100","105"],"answer":"100","type":"quant","difficulty":"easy"},
{"q":"What is 20% of 50?","options":["5","10","15","20"],"answer":"10","type":"quant","difficulty":"easy"},
{"q":"What is 500 - 200?","options":["200","250","300","350"],"answer":"300","type":"quant","difficulty":"easy"},


{"q":"Find the next number in the series: 2, 4, 6, 8, ?","options":["9","10","11","12"],"answer":"10","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 5, 10, 15, 20, ?","options":["22","24","25","30"],"answer":"25","type":"logic","difficulty":"easy"},
{"q":"Which number is missing: 1, 3, 5, ?, 9","options":["6","7","8","10"],"answer":"7","type":"logic","difficulty":"easy"},
{"q":"Find the odd one out: Dog, Cat, Cow, Car","options":["Dog","Cat","Cow","Car"],"answer":"Car","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 10, 20, 30, ?","options":["35","40","45","50"],"answer":"40","type":"logic","difficulty":"easy"},

{"q":"Which is the odd one: Apple, Banana, Mango, Potato","options":["Apple","Banana","Mango","Potato"],"answer":"Potato","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 3, 6, 9, 12, ?","options":["14","15","16","18"],"answer":"15","type":"logic","difficulty":"easy"},
{"q":"Find the missing number: 2, 3, 5, 7, ?","options":["9","10","11","12"],"answer":"11","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 100, 90, 80, ?","options":["60","70","75","85"],"answer":"70","type":"logic","difficulty":"easy"},
{"q":"Find the odd one: Rose, Lily, Lotus, Table","options":["Rose","Lily","Lotus","Table"],"answer":"Table","type":"logic","difficulty":"easy"},

{"q":"Find the next number: 1, 2, 3, 4, ?","options":["5","6","7","8"],"answer":"5","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 7, 14, 21, ?","options":["24","28","30","35"],"answer":"28","type":"logic","difficulty":"easy"},
{"q":"Which is different: Pen, Pencil, Book, Chair","options":["Pen","Pencil","Book","Chair"],"answer":"Chair","type":"logic","difficulty":"easy"},
{"q":"Find the next number: 11, 22, 33, ?","options":["40","44","45","50"],"answer":"44","type":"logic","difficulty":"easy"},
{"q":"Find the missing number: 9, 18, ?, 36","options":["20","24","27","30"],"answer":"27","type":"logic","difficulty":"easy"},

{"q":"Find the next number: 2, 5, 8, 11, ?","options":["12","13","14","15"],"answer":"14","type":"logic","difficulty":"easy"},
{"q":"Find the odd one: Car, Bus, Train, Banana","options":["Car","Bus","Train","Banana"],"answer":"Banana","type":"logic","difficulty":"easy"},
{"q":"Find next: 50, 100, 150, ?","options":["180","200","220","250"],"answer":"200","type":"logic","difficulty":"easy"},
{"q":"Find next: 8, 16, 24, ?","options":["30","32","34","36"],"answer":"32","type":"logic","difficulty":"easy"},
{"q":"Find missing: 4, 8, ?, 16","options":["10","12","14","15"],"answer":"12","type":"logic","difficulty":"easy"},

{"q":"Find next: 6, 12, 18, ?","options":["20","22","24","26"],"answer":"24","type":"logic","difficulty":"easy"},
{"q":"Find odd: Tiger, Lion, Cow, Dog","options":["Tiger","Lion","Cow","Dog"],"answer":"Cow","type":"logic","difficulty":"easy"},
{"q":"Find next: 9, 18, 27, ?","options":["30","32","36","40"],"answer":"36","type":"logic","difficulty":"easy"},
{"q":"Find missing: 1, 4, ?, 16","options":["6","8","9","12"],"answer":"9","type":"logic","difficulty":"easy"},
{"q":"Find next: 20, 40, 60, ?","options":["70","75","80","90"],"answer":"80","type":"logic","difficulty":"easy"},


{"q":"Choose the correct word: He ___ playing.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy"},
{"q":"Choose the synonym of 'Happy'.","options":["Sad","Joyful","Angry","Tired"],"answer":"Joyful","type":"verbal","difficulty":"easy"},
{"q":"Choose the antonym of 'Big'.","options":["Large","Huge","Small","Wide"],"answer":"Small","type":"verbal","difficulty":"easy"},
{"q":"Fill in the blank: She ___ a teacher.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy"},
{"q":"Choose the correct spelling.","options":["Recieve","Receive","Recive","Receve"],"answer":"Receive","type":"verbal","difficulty":"easy"},

{"q":"Choose synonym of 'Fast'.","options":["Slow","Quick","Late","Lazy"],"answer":"Quick","type":"verbal","difficulty":"easy"},
{"q":"Choose antonym of 'Cold'.","options":["Hot","Cool","Warm","Freeze"],"answer":"Hot","type":"verbal","difficulty":"easy"},
{"q":"Fill: They ___ going home.","options":["is","are","am","be"],"answer":"are","type":"verbal","difficulty":"easy"},
{"q":"Choose correct article: ___ apple","options":["a","an","the","no"],"answer":"an","type":"verbal","difficulty":"easy"},
{"q":"Plural of 'Book'","options":["Book","Books","Bookes","Books"],"answer":"Books","type":"verbal","difficulty":"easy"},

{"q":"Choose synonym of 'Strong'.","options":["Weak","Powerful","Small","Thin"],"answer":"Powerful","type":"verbal","difficulty":"easy"},
{"q":"Choose antonym of 'Old'.","options":["New","Ancient","Past","Used"],"answer":"New","type":"verbal","difficulty":"easy"},
{"q":"Fill: I ___ a student.","options":["is","are","am","be"],"answer":"am","type":"verbal","difficulty":"easy"},
{"q":"Choose correct: She ___ singing.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy"},
{"q":"Plural of 'Child'","options":["Childs","Children","Childes","Child"],"answer":"Children","type":"verbal","difficulty":"easy"},

{"q":"Choose synonym of 'Easy'.","options":["Hard","Simple","Tough","Complex"],"answer":"Simple","type":"verbal","difficulty":"easy"},
{"q":"Choose antonym of 'Up'.","options":["Down","Top","Above","Over"],"answer":"Down","type":"verbal","difficulty":"easy"},
{"q":"Fill: We ___ friends.","options":["is","are","am","be"],"answer":"are","type":"verbal","difficulty":"easy"},
{"q":"Choose correct spelling.","options":["Adress","Address","Adres","Addres"],"answer":"Address","type":"verbal","difficulty":"easy"},
{"q":"Plural of 'Pen'","options":["Pen","Pens","Penes","Penses"],"answer":"Pens","type":"verbal","difficulty":"easy"},

{"q":"Choose synonym of 'Cold'.","options":["Hot","Cool","Warm","Boil"],"answer":"Cool","type":"verbal","difficulty":"easy"},
{"q":"Choose antonym of 'Near'.","options":["Far","Close","Next","Beside"],"answer":"Far","type":"verbal","difficulty":"easy"},
{"q":"Fill: He ___ my brother.","options":["is","are","am","be"],"answer":"is","type":"verbal","difficulty":"easy"},
{"q":"Choose correct article: ___ umbrella","options":["a","an","the","no"],"answer":"an","type":"verbal","difficulty":"easy"},
{"q":"Plural of 'Car'","options":["Car","Cars","Cares","Carses"],"answer":"Cars","type":"verbal","difficulty":"easy"},


{"q":"A value increases from 100 to 200. What is the increase?","options":["50","100","150","200"],"answer":"100","type":"di","difficulty":"easy"},
{"q":"Find 50% of 400.","options":["100","150","200","250"],"answer":"200","type":"di","difficulty":"easy"},
{"q":"Profit = ₹100, Cost = ₹400. What is profit %?","options":["20%","25%","30%","35%"],"answer":"25%","type":"di","difficulty":"easy"},
{"q":"Loss = ₹50, Cost = ₹250. What is loss %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Increase from 200 to 300. % increase?","options":["25%","50%","75%","100%"],"answer":"50%","type":"di","difficulty":"easy"},

{"q":"Find 25% of 200.","options":["25","50","75","100"],"answer":"50","type":"di","difficulty":"easy"},
{"q":"Profit ₹200 on cost ₹1000. Profit %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Loss ₹20 on cost ₹100. Loss %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Increase from 500 to 600. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Find 10% of 500.","options":["40","50","60","70"],"answer":"50","type":"di","difficulty":"easy"},

{"q":"Profit ₹50 on cost ₹250. Profit %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Loss ₹30 on cost ₹150. Loss %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Increase from 300 to 360. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Find 20% of 250.","options":["40","50","60","70"],"answer":"50","type":"di","difficulty":"easy"},
{"q":"Profit ₹80 on ₹400. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},

{"q":"Loss ₹40 on ₹200. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Increase 100→150. %?","options":["25%","50%","75%","100%"],"answer":"50%","type":"di","difficulty":"easy"},
{"q":"Find 30% of 100.","options":["20","25","30","35"],"answer":"30","type":"di","difficulty":"easy"},
{"q":"Profit ₹60 on ₹300. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Loss ₹25 on ₹125. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},

{"q":"Increase 400→480. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Find 40% of 200.","options":["60","70","80","90"],"answer":"80","type":"di","difficulty":"easy"},
{"q":"Profit ₹120 on ₹600. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Loss ₹10 on ₹50. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},
{"q":"Increase 250→300. %?","options":["10%","15%","20%","25%"],"answer":"20%","type":"di","difficulty":"easy"},


{"q":"A train of length 120 meters crosses a pole in 6 seconds. What is its speed in km/h?","options":["60","72","80","90"],"answer":"72","type":"quant","difficulty":"medium"},
{"q":"Find the simple interest on ₹5000 at 6% per annum for 3 years.","options":["800","850","900","950"],"answer":"900","type":"quant","difficulty":"medium"},
{"q":"A shop offers a 10% discount on an item priced at ₹800. What is the final price?","options":["680","700","720","750"],"answer":"720","type":"quant","difficulty":"medium"},
{"q":"What is the compound interest on ₹1000 at 10% for 2 years?","options":["200","210","220","250"],"answer":"210","type":"quant","difficulty":"medium"},
{"q":"If the ratio of A to B is 2:3 and their sum is 50, what is the value of A?","options":["20","25","30","35"],"answer":"20","type":"quant","difficulty":"medium"},

{"q":"A number increased by 20% becomes 120. What is the original number?","options":["90","95","100","105"],"answer":"100","type":"quant","difficulty":"medium"},
{"q":"Find the average of the numbers 10, 20, 30, 40, and 50.","options":["25","30","35","40"],"answer":"30","type":"quant","difficulty":"medium"},
{"q":"A product is marked at ₹1000 and sold at a 20% profit. What is the cost price?","options":["700","750","800","850"],"answer":"800","type":"quant","difficulty":"medium"},
{"q":"What is the value of 15 × 12?","options":["160","170","180","190"],"answer":"180","type":"quant","difficulty":"medium"},
{"q":"A man spends 40% of his salary and saves ₹6000. What is his salary?","options":["9000","10000","12000","15000"],"answer":"10000","type":"quant","difficulty":"medium"},

{"q":"Find the LCM of 12 and 18.","options":["24","30","36","42"],"answer":"36","type":"quant","difficulty":"medium"},
{"q":"Find the HCF of 24 and 36.","options":["6","8","12","18"],"answer":"12","type":"quant","difficulty":"medium"},
{"q":"What is 20% of 250?","options":["40","45","50","55"],"answer":"50","type":"quant","difficulty":"medium"},
{"q":"If a car travels 60 km in 2 hours, what is its speed?","options":["20 km/h","25 km/h","30 km/h","35 km/h"],"answer":"30 km/h","type":"quant","difficulty":"medium"},
{"q":"Find the square of 15.","options":["200","225","250","275"],"answer":"225","type":"quant","difficulty":"medium"},


{"q":"Find the next number in the series: 3, 6, 12, 24, ?","options":["36","42","48","60"],"answer":"48","type":"logic","difficulty":"medium"},
{"q":"Find the missing number: 5, 10, 20, ?, 80","options":["30","35","40","50"],"answer":"40","type":"logic","difficulty":"medium"},
{"q":"Which number replaces the question mark: 2, 6, 18, 54, ?","options":["108","120","162","180"],"answer":"162","type":"logic","difficulty":"medium"},
{"q":"Find the odd one out: 2, 3, 5, 7, 9, 11","options":["2","3","9","11"],"answer":"9","type":"logic","difficulty":"medium"},
{"q":"Find the next number: 1, 4, 9, 16, ?","options":["20","24","25","30"],"answer":"25","type":"logic","difficulty":"medium"},

{"q":"Find the next number: 7, 14, 28, 56, ?","options":["84","96","112","120"],"answer":"112","type":"logic","difficulty":"medium"},
{"q":"Which word does not belong: Apple, Mango, Banana, Carrot","options":["Apple","Mango","Banana","Carrot"],"answer":"Carrot","type":"logic","difficulty":"medium"},
{"q":"Find the missing number: 10, 15, 25, 40, ?","options":["55","60","65","70"],"answer":"65","type":"logic","difficulty":"medium"},
{"q":"Find the next number: 100, 50, 25, ?","options":["5","10","12","15"],"answer":"12.5","type":"logic","difficulty":"medium"},
{"q":"Which number comes next: 4, 8, 15, 16, 23, ?","options":["30","32","35","36"],"answer":"42","type":"logic","difficulty":"medium"},

{"q":"Find the next number: 11, 22, 44, 88, ?","options":["132","144","160","176"],"answer":"176","type":"logic","difficulty":"medium"},
{"q":"Find the missing number: 3, 9, 27, ?, 243","options":["54","60","81","100"],"answer":"81","type":"logic","difficulty":"medium"},
{"q":"Find the odd one: Circle, Square, Triangle, Sphere","options":["Circle","Square","Triangle","Sphere"],"answer":"Sphere","type":"logic","difficulty":"medium"},
{"q":"Find next: 6, 11, 21, 36, ?","options":["50","51","53","56"],"answer":"56","type":"logic","difficulty":"medium"},
{"q":"Find the next number: 2, 8, 18, 32, ?","options":["48","50","54","60"],"answer":"50","type":"logic","difficulty":"medium"},


{"q":"Choose the correct sentence: He does not ___ the answer.","options":["know","knows","knowing","knew"],"answer":"know","type":"verbal","difficulty":"medium"},
{"q":"Choose the synonym of 'Rapid'.","options":["Slow","Quick","Late","Soft"],"answer":"Quick","type":"verbal","difficulty":"medium"},
{"q":"Choose the antonym of 'Expand'.","options":["Grow","Increase","Shrink","Extend"],"answer":"Shrink","type":"verbal","difficulty":"medium"},
{"q":"Fill in the blank: She has ___ her homework.","options":["done","do","did","doing"],"answer":"done","type":"verbal","difficulty":"medium"},
{"q":"Choose the correct spelling.","options":["Accomodate","Acommodate","Accommodate","Acomodate"],"answer":"Accommodate","type":"verbal","difficulty":"medium"},

{"q":"Choose synonym of 'Begin'.","options":["Start","End","Stop","Pause"],"answer":"Start","type":"verbal","difficulty":"medium"},
{"q":"Choose antonym of 'Increase'.","options":["Raise","Grow","Decrease","Expand"],"answer":"Decrease","type":"verbal","difficulty":"medium"},
{"q":"Fill: They ___ already finished.","options":["has","have","had","having"],"answer":"have","type":"verbal","difficulty":"medium"},
{"q":"Choose correct: She is ___ than her sister.","options":["tall","taller","tallest","more tall"],"answer":"taller","type":"verbal","difficulty":"medium"},
{"q":"Plural of 'Analysis'.","options":["Analysises","Analyses","Analysis","Analys"],"answer":"Analyses","type":"verbal","difficulty":"medium"},

{"q":"A number when increased by 25% becomes 125. What is the original number?","options":["80","90","100","110"],"answer":"100","type":"quant","difficulty":"medium"},
{"q":"Find the value of 25 × 16.","options":["350","375","400","425"],"answer":"400","type":"quant","difficulty":"medium"},
{"q":"A man earns ₹15000 and spends 60%. How much does he save?","options":["5000","6000","7000","8000"],"answer":"6000","type":"quant","difficulty":"medium"},
{"q":"Find the next number: 9, 18, 36, 72, ?","options":["120","130","144","150"],"answer":"144","type":"logic","difficulty":"medium"},
{"q":"Which number completes the pattern: 1, 3, 6, 10, ?","options":["12","14","15","16"],"answer":"15","type":"logic","difficulty":"medium"},

{"q":"Find the missing number: 2, 5, 11, 23, ?","options":["35","41","47","51"],"answer":"47","type":"logic","difficulty":"medium"},
{"q":"Choose the correct word: She ___ to the market yesterday.","options":["go","gone","went","going"],"answer":"went","type":"verbal","difficulty":"medium"},
{"q":"Choose synonym of 'Difficult'.","options":["Hard","Easy","Simple","Soft"],"answer":"Hard","type":"verbal","difficulty":"medium"},
{"q":"Choose antonym of 'Bright'.","options":["Light","Dark","Shiny","Clear"],"answer":"Dark","type":"verbal","difficulty":"medium"},
{"q":"Fill in the blank: He has ___ the work.","options":["complete","completed","completing","completes"],"answer":"completed","type":"verbal","difficulty":"medium"},

{"q":"Two pipes fill a tank in 12 hours and 18 hours respectively. How long will they take together?","options":["7.2","7.5","8","9"],"answer":"7.2","type":"quant","difficulty":"hard"},
{"q":"A train crosses a 300 m platform in 30 seconds at 54 km/h. Find the length of the train.","options":["150 m","200 m","250 m","300 m"],"answer":"150 m","type":"quant","difficulty":"hard"},
{"q":"Find compound interest on ₹4000 at 10% for 2 years.","options":["800","820","840","880"],"answer":"840","type":"quant","difficulty":"hard"},
{"q":"A sum becomes ₹6600 in 2 years and ₹7260 in 3 years under simple interest. Find principal.","options":["5000","5500","6000","6500"],"answer":"6000","type":"quant","difficulty":"hard"},
{"q":"Ratio of ages of A and B is 4:7, sum is 55. Find A's age.","options":["20","22","24","28"],"answer":"20","type":"quant","difficulty":"hard"},

{"q":"A shopkeeper marks goods 30% above cost and gives 10% discount. Find profit %.","options":["15%","17%","18%","20%"],"answer":"17%","type":"quant","difficulty":"hard"},
{"q":"HCF of two numbers is 15 and LCM is 225. One number is 45. Find the other.","options":["50","60","75","90"],"answer":"75","type":"quant","difficulty":"hard"},
{"q":"A can do a work in 8 days, B in 12 days. After 2 days A leaves. Remaining work done by B in how many days?","options":["3","4","5","6"],"answer":"4","type":"quant","difficulty":"hard"},
{"q":"A number increased by 25% and decreased by 20%. Net change?","options":["0%","1% increase","2% decrease","5% increase"],"answer":"0%","type":"quant","difficulty":"hard"},
{"q":"Square root of 1764 is?","options":["40","42","44","46"],"answer":"42","type":"quant","difficulty":"hard"},

{"q":"Boat speed is 10 km/h, stream is 2 km/h. Downstream speed?","options":["10","11","12","13"],"answer":"12","type":"quant","difficulty":"hard"},
{"q":"Find (20² - 10²).","options":["200","300","400","500"],"answer":"300","type":"quant","difficulty":"hard"},
{"q":"If 30% of a number is 90, find the number.","options":["200","250","300","350"],"answer":"300","type":"quant","difficulty":"hard"},
{"q":"Compound interest on ₹2000 at 5% for 2 years?","options":["200","205","210","215"],"answer":"205","type":"quant","difficulty":"hard"},
{"q":"Value of log10(10000)?","options":["2","3","4","5"],"answer":"4","type":"quant","difficulty":"hard"},

{"q":"If a sum doubles in 4 years, rate of interest?","options":["12.5%","15%","18%","20%"],"answer":"25%","type":"quant","difficulty":"hard"},
{"q":"Find value of (1/2 + 1/4 + 1/8).","options":["7/8","5/8","3/4","1"],"answer":"7/8","type":"quant","difficulty":"hard"},
{"q":"A alone completes work in 10 days, B in 15 days. Together for 2 days then A leaves. B completes remaining in?","options":["4","5","6","7"],"answer":"5","type":"quant","difficulty":"hard"},
{"q":"Cube root of 1331?","options":["9","10","11","12"],"answer":"11","type":"quant","difficulty":"hard"},
{"q":"Remainder when square of number leaves remainder 4 when divided by 5?","options":["1","2","3","4"],"answer":"4","type":"quant","difficulty":"hard"},


{"q":"Find next: 2, 5, 10, 17, 26, ?","options":["35","36","37","38"],"answer":"37","type":"logic","difficulty":"hard"},
{"q":"Find missing: 3, 8, 15, 24, 35, ?","options":["46","48","49","50"],"answer":"48","type":"logic","difficulty":"hard"},
{"q":"Find next: 1, 4, 10, 22, 46, ?","options":["94","92","90","96"],"answer":"94","type":"logic","difficulty":"hard"},
{"q":"Odd one: 4, 9, 16, 25, 30","options":["4","9","16","30"],"answer":"30","type":"logic","difficulty":"hard"},
{"q":"Find next: 3, 12, 48, 192, ?","options":["576","600","650","700"],"answer":"768","type":"logic","difficulty":"hard"},

{"q":"Find missing: 7, 10, 16, 28, 52, ?","options":["100","104","108","112"],"answer":"100","type":"logic","difficulty":"hard"},
{"q":"Find next: 5, 11, 23, 47, ?","options":["95","96","97","98"],"answer":"95","type":"logic","difficulty":"hard"},
{"q":"Find next: 2, 7, 26, 101, ?","options":["404","405","406","407"],"answer":"406","type":"logic","difficulty":"hard"},
{"q":"Find missing: 9, 18, 36, 72, ?","options":["120","132","144","156"],"answer":"144","type":"logic","difficulty":"hard"},
{"q":"Find next: 1, 3, 7, 15, 31, ?","options":["55","60","63","65"],"answer":"63","type":"logic","difficulty":"hard"},

{"q":"Find odd one: 2, 6, 12, 20, 30, 42","options":["2","6","20","42"],"answer":"42","type":"logic","difficulty":"hard"},
{"q":"Find next: 4, 16, 64, 256, ?","options":["512","768","1024","2048"],"answer":"1024","type":"logic","difficulty":"hard"},
{"q":"Find missing: 11, 13, 17, 19, 23, ?","options":["25","27","29","31"],"answer":"29","type":"logic","difficulty":"hard"},
{"q":"Find next: 6, 24, 60, 120, ?","options":["180","210","240","300"],"answer":"210","type":"logic","difficulty":"hard"},
{"q":"Find next: 1, 2, 6, 24, 120, 720, ?","options":["3600","5000","7200","5040"],"answer":"5040","type":"logic","difficulty":"hard"},


{"q":"Choose correct: Neither of the boys ___ present.","options":["is","are","were","be"],"answer":"is","type":"verbal","difficulty":"hard"},
{"q":"Synonym of 'Benevolent'.","options":["Kind","Harsh","Rude","Cold"],"answer":"Kind","type":"verbal","difficulty":"hard"},
{"q":"Antonym of 'Scarce'.","options":["Rare","Plenty","Less","Small"],"answer":"Plenty","type":"verbal","difficulty":"hard"},
{"q":"Fill: Hardly had she entered ___ the bell rang.","options":["than","when","then","while"],"answer":"when","type":"verbal","difficulty":"hard"},
{"q":"Correct spelling.","options":["Pronounciation","Pronunciation","Pronuncation","Prononciation"],"answer":"Pronunciation","type":"verbal","difficulty":"hard"},

{"q":"Synonym of 'Resilient'.","options":["Flexible","Weak","Fragile","Rigid"],"answer":"Flexible","type":"verbal","difficulty":"hard"},
{"q":"Antonym of 'Explicit'.","options":["Clear","Hidden","Obvious","Direct"],"answer":"Hidden","type":"verbal","difficulty":"hard"},
{"q":"Fill: She had ___ finished before he arrived.","options":["already","yet","still","ever"],"answer":"already","type":"verbal","difficulty":"hard"},
{"q":"Choose correct: Each of the students ___ responsible.","options":["is","are","were","be"],"answer":"is","type":"verbal","difficulty":"hard"},
{"q":"Plural of 'Thesis'.","options":["Thesises","Theses","Thesis","Theis"],"answer":"Theses","type":"verbal","difficulty":"hard"},
{"q":"A sum of money becomes ₹8000 in 2 years and ₹9200 in 3 years under simple interest. Find the principal.","options":["6000","6500","7000","7500"],"answer":"6000","type":"quant","difficulty":"hard"},

{"q":"Find the next number: 9, 27, 81, 243, ?","options":["486","729","512","1024"],"answer":"729","type":"logic","difficulty":"hard"},

{"q":"If the ratio of two numbers is 5:7 and their difference is 24, find the larger number.","options":["42","56","70","84"],"answer":"84","type":"quant","difficulty":"hard"},

{"q":"Choose the correct sentence: 'He is one of the players who ___ selected for the team.'","options":["is","are","was","be"],"answer":"are","type":"verbal","difficulty":"hard"},

{"q":"Find the next letter series: A, C, F, J, O, ?","options":["T","U","V","W"],"answer":"U","type":"logic","difficulty":"hard"}

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

    return psycopg.connect(db_url, sslmode='require')


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
