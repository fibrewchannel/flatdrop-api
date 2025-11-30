import openai
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Check your .env file.")

# Construct the GitHub raw URL
url = "https://raw.githubusercontent.com/fibrewchannel/flatline-codex/gh-pages/_inload/docs/recovery/share_draft_hope_section.md"
response = requests.get(url)

if response.status_code == 200:
    file_content = response.text

    # Send file content to GPT-4 for analysis
    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a memoir architect analyzing markdown files for narrative clustering."},
            {"role": "user", "content": f"Here's a markdown file from the Flatline Codex:\n\n{file_content}\n\nCan you identify the Structure, Transmission, Purpose, and Terrain coordinates?"},
        ]
    )

    print(chat_completion['choices'][0]['message']['content'])
else:
    print(f"Error fetching file: {response.status_code}")
