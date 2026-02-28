import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

prompt = """
You are an expert Software Auditor detecting plagiarism and assessing code originality.
Analyze the following GitHub repository and code samples to determine if this project represents original software engineering work, or if it appears to be a copy-paste job, a standard framework boilerplate, or a common tutorial clone (e.g., standard "To-Do app" or "Blogging engine").

Repository Name: test/test-repo
Description: A test repository

Code Samples from Core Files:
--- test_file.py ---
def test():
    pass

Please provide your assessment strictly in Turkish.

Return ONLY a JSON object with the following keys:
- "score": An integer from 0 to 100 (100 = Highly original architecture/logic, 0 = 100% boilerplate/tutorial copy).
- "assessment": A short 3-4 word classification (e.g. "Highly Original", "Tutorial Clone", "Standard Boilerplate").
- "explanation": A 2 sentence explanation of your reasoning.
"""

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    print("--- RAW RESPONSE ---")
    print(response.text)
    print("--- END RAW ---")
    
    text = response.text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    
    import json
    parsed = json.loads(text.strip())
    print("Parsed JSON successfully:", parsed)
except Exception as e:
    import traceback
    traceback.print_exc()
