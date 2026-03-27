from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        message TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_to_db(user_id, role, message):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_history (user_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, role, message, str(datetime.now()))
    )

    conn.commit()
    conn.close()


init_db()

# ---------------- CONFIG ----------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

# ---------------- MEMORY ----------------
summary_memory = {}
intent_memory = {}

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are a Mentor Connect assistant.

Rules:
- Keep answers short (2-5 lines max)
- Be friendly and professional
- If unclear, ask a follow-up question
- Help users with mentoring and general queries
"""

# ---------------- INTENT ----------------
def detect_intent(user_id, message):
    msg = message.lower()

    # ✅ RULE-BASED CHECK (VERY IMPORTANT)
    if any(q in msg for q in ["what", "how", "why", "explain", "define"]):
        return "general_question"

    if any(k in msg for k in ["mentor", "help", "guidance"]):
        return "find_mentor"

    # 🤖 fallback to LLM
    summary = summary_memory.get(user_id, "")

    prompt = [
        {"role": "system", "content": "Return only: find_mentor OR general_question"},
        {"role": "user", "content": f"Summary: {summary}\nMessage: {message}"}
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=prompt
    )

    return response.choices[0].message.content.strip().lower()


# ---------------- SUMMARY ----------------
def update_summary(user_id, message):
    current_summary = summary_memory.get(user_id, "")

    prompt = [
        {"role": "system", "content": "Update summary in 1 line only"},
        {"role": "user", "content": f"Current: {current_summary}\nNew: {message}"}
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=prompt
    )

    updated = response.choices[0].message.content.strip()
    summary_memory[user_id] = updated
    return updated


# ---------------- MENTOR ----------------
def call_recommendation(query):
    return [
        {"name": "Rahul", "skill": "React", "experience": "5 years"},
        {"name": "Anita", "skill": "Frontend", "experience": "4 years"}
    ]


# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id")
    message = data.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id and message required"}), 400

    # STEP 1: update summary
    summary = update_summary(user_id, message)

    # STEP 2: detect fresh intent ALWAYS
    new_intent = detect_intent(user_id, message)

    # STEP 3: smart intent handling
    if new_intent == "find_mentor":
        intent_memory[user_id] = "find_mentor"
    elif new_intent == "general_question":
        intent_memory[user_id] = "general_question"

    intent = intent_memory.get(user_id, new_intent)

    # STEP 4: mentor flow
    if intent == "find_mentor":
        mentors = call_recommendation(summary)

        text = "Here are some mentors:\n"
        for m in mentors:
            text += f"{m['name']} - {m['skill']} ({m['experience']})\n"

        return jsonify({
            "intent": intent,
            "response": text
        })

    # STEP 5: general question
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Summary: {summary}"},
        {"role": "user", "content": message}
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    reply = response.choices[0].message.content

    save_to_db(user_id, "user", message)
    save_to_db(user_id, "assistant", reply)

    return jsonify({
        "intent": intent,
        "response": reply
    })


# ---------------- RESET ----------------
@app.route("/reset", methods=["POST"])
def reset():
    data = request.json
    user_id = data.get("user_id")

    summary_memory[user_id] = ""
    intent_memory[user_id] = ""

    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "reset done"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)