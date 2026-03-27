# Mentor Chatbot

This is a Flask-based chatbot built for Mentor Connect.

## Features
- Intent Detection (find_mentor / general_question)
- Summary-based memory (no full chat history)
- Mentor recommendation system
- Clean and short responses

## Tech Stack
- Python (Flask)
- Groq API (LLM)
- SQLite

## How to Run

1. Install dependencies
pip install flask groq python-dotenv

2. Add .env file
GROQ_API_KEY=your_api_key

3. Run server
python app.py

4. Test API
POST http://127.0.0.1:5000/chat
