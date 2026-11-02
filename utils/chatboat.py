import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_chat_response(message, subjects):

    subject_list = ", ".join(
        s.get("subject", "")
        for s in subjects
    ) if subjects else "No subjects"

    prompt = f"""
You are NOVA AI Tutor.

Current Subjects:
{subject_list}

Student Question:
{message}

Rules:
- Explain concepts in simple English.
- Generate MCQs if asked.
- Generate study plans if asked.
- Be friendly and concise.
"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        return response.text

    except Exception as e:
        return f"Gemini Error: {str(e)}"