from flask import Flask, request, jsonify
import openai
import datetime
import json
import os
import smtplib
from email.message import EmailMessage
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = "sk-your-real-openai-key-here"
EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"
TARGET_EMAIL = "student_email@example.com"
progress_file = "student_progress.json"

if not os.path.exists(progress_file):
    with open(progress_file, "w") as f:
        json.dump({}, f)


def build_prompt(subject, level, question, student_answer):
    return f"""You are a highly intelligent and empathetic AI tutor who assists students across all academic subjects and levels.

The student is studying **{subject}** at a **{level}** level.
They submitted this question: "{question}"
And their final answer is: "{student_answer}"

Your role is to:
1. Identify what method or reasoning the student may have used to arrive at this answer.
2. If there are flaws in the approach or answer, kindly explain the mistake and why it may seem logical at first.
3. Reteach the correct method step-by-step, using clear language and relatable examples tailored to the subject.
4. Provide constructive feedback and praise the student's effort and intent to learn.
5. Recommend 1-2 short homework tasks the student can do next to strengthen their understanding.
6. Maintain a supportive, friendly tone that feels like a human tutor."""


def update_progress(subject, level):
    with open(progress_file, "r") as f:
        progress = json.load(f)
    if subject not in progress:
        progress[subject] = {}
    if level not in progress[subject]:
        progress[subject][level] = 0
    progress[subject][level] += 1
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=4)


def send_email_reminder(subject, level, response):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Your {subject} Study Summary - Level: {level}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TARGET_EMAIL
        msg.set_content(f"Great job today studying {subject} at {level} level!")
        msg.add_alternative(f"""<html>
  <body>
    <h2>Keep it up!</h2>
    <p><strong>Level:</strong> {level}</p>
    <p><strong>AI Tutor Feedback:</strong></p>
    <pre>{response}</pre>
    <p>See you next study session!</p>
  </body>
</html>
""", subtype='html')
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("[Email Error]", str(e))


@app.route("/tutor", methods=["POST"])
def tutor():
    data = request.json
    subject = data.get("subject")
    level = data.get("level")
    question = data.get("question")
    answer = data.get("answer")
    prompt = build_prompt(subject, level, question, answer)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response['choices'][0]['message']['content']
        update_progress(subject, level)
        send_email_reminder(subject, level, reply)
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/progress", methods=["GET"])
def get_progress():
    with open(progress_file, "r") as f:
        progress = json.load(f)
    return jsonify(progress)


if __name__ == "__main__":
    app.run(debug=True)
