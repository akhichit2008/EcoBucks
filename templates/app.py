import os
from dotenv import load_dotenv
import google.generativeai as genai
load_dotenv()
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY'] 
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
response = model.generate_model("Write me a poem")
print(response.text)