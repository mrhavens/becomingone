import requests
import json
import sys

def submit_issue(token, repo, title, body, labels=None, assignees=None):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    if labels:
        data["labels"] = labels
    if assignees:
        data["assignees"] = assignees

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Successfully created issue: {response.json().get('html_url')}")
    else:
        print(f"Failed to create issue: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 submit_issue.py <token> <repo> <title_file> <body_file>")
        sys.exit(1)
    
    token = sys.argv[1]
    repo = sys.argv[2]
    title_file = sys.argv[3]
    body_file = sys.argv[4]
    
    with open(title_file, 'r') as f:
        title = f.read().strip()
    
    with open(body_file, 'r') as f:
        body = f.read()
        
    submit_issue(token, repo, title, body, labels=["peer-review", "academic-rigor"], assignees=["mrhavens"])
