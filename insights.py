import requests
import json
from app import read_sessions, read_recent_logs
 
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"
LOG_FILE = "data/logs.json"
 
 
def read_recent_logs(n=20):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    logs = [json.loads(line) for line in lines[-n:]]
    return logs
 
def generate_prompt(log_data):
    return f"""You are an AI productivity assistant. The following is the user's recent app usage data:
 
{json.dumps(log_data, indent=2)}
 
Based on this, suggest 3 specific and actionable productivity improvements."""
 

def give_timer_suggestions():
    sessions_data = read_sessions()
    log_data = read_recent_logs()

    prompt = f"""You are an AI productivity assistant. The following is the user's recent app usage data:
 
        {json.dumps(log_data, indent=2)}

        The follow is the user's session data:

        {json.dumps(sessions_data, indent=2)}
        
        Based on these two sets of data, suggest:
        1. An optimal break reminder interval.
        2. Idle app alert thresholds (3 levels, in minutes).
        3. Give me feedback on how my productivity has been. What are some positives and possible areas to improve in? 
            Specifically keep in mind this most recent session in relation to the rest of the previous sessions, if any exist.
        4. Three specific and actionable productivity improvements based on the feedback.
    """ + r"""
        Format your response as JSON:
            {
            "break_threshold": "<suggested optimal break reminder interval in minutes as an integer>",
            "idle_app_threshold_1": "level 1 idle app alert threshold in minutes as an integer",
            "idle_app_threshold_2": "level 2 idle app alert threshold in minutes as an integer",
            "idle_app_threshold_3": "level 3 idle app alert threshold in minutes as an integer",
            "feedback": "session feedback"
            "improvements": ["3 actionable productivity improvements"]
            }
    """

    return ask_llm(prompt)

def ask_llm(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]
 
def main():
    suggestions = give_timer_suggestions()
    # log_data = read_recent_logs()
    # prompt = generate_prompt(log_data)
    # suggestions = ask_llm(prompt)
    print("\n[Productivity Suggestions]\n")
    print(suggestions)
 
if __name__ == "__main__":
    main()
