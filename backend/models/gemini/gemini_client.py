import google.generativeai as genai
from configs.settings import GEMINI_API_KEY


genai.configure(api_key=GEMINI_API_KEY)


def chat_with_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(prompt)

    return response.text