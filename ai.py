import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')


res = {"How do you primarily power your home?":"Natural Gas","How often do you use public transportation, carpool, or bike instead of driving alone?":"Daily","What type of vehicle do you drive?":"Gasoline Vehicle"}
def calculate_initial_score(responses):
    res = model.generate_content(f"Based on the actions performed by the user as mentioned in this list {responses} of responses to different questions from a sustainability living stand point. The score should be the only output (out of 100). Input is given in the form of dictionary (for your convinience) with key representing question and value representing user's response to that particular question")
    return res.text

def suggest_daily_tasks(score):
    res = model.generate_content(f"Based on this score {score} out of 100 (It shows the sustainbility score of a user based on his daily practices. Suggest some daily tasks for him that he can perform to increase the score. The output should be strictly in points and one sentence and only 4 points allowed")
    return res.text

def check_submission(image,task):
    model = genai.GenerativeModel('gemini-1.5-flash')
    res = model.generate_content([f'is this a correct user-submission proof image for this sustainbility task: {task} ? (tell me yes or no other outputs not needed just one word)',image])
    if "yes" in res.text.lower():
        return True
    else:
        return False
    
def calculate_based_data(data):
    pass

suggest_daily_tasks(80)