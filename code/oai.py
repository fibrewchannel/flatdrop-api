import openai
import requests

# Set this to your actual OpenAI key
openai.api_key = "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"

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
