import requests
import json
 
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
 
def ask_llm(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]
 
def main():
    log_data = read_recent_logs()
    prompt = generate_prompt(log_data)
    suggestions = ask_llm(prompt)
    print("\n[Productivity Suggestions]\n")
    print(suggestions)
 
if __name__ == "__main__":
    main()
