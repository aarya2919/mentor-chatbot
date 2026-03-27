from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

api_key = os.getenv("GROQ_API_KEY")

print("API KEY:", api_key)   

client = Groq(api_key=api_key)

user_prompt = input("Enter your prompt: ")

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "system",
            "content": "You are an AI assistant for a platform called Mentor Connect. This platform helps students connect with mentors for career guidance, project help, and skill development. Answer all questions related to mentorship, learning, career growth, and project guidance in a simple and helpful way."
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
)

print("\nOutput:")
print(response.choices[0].message.content)