import requests
import sys
import json
import yaml
import os
from openai import OpenAI

# 🔐 Use env var or hardcode your key
api_key = os.getenv("OPENAI_API_KEY", "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")
client = OpenAI(api_key=api_key)

# ✅ Grab URL from command line
if len(sys.argv) < 2:
    print("Usage: python ingest_github_markdown.py <raw_github_markdown_url>")
    sys.exit(1)

url = sys.argv[1]

# 🌐 Fetch Markdown file from GitHub
print(f"📥 Fetching content from: {url}")
res = requests.get(url)
if res.status_code != 200:
    print(f"❌ Failed to fetch: {res.status_code}")
    sys.exit(2)

markdown = res.text

# 🧠 Build OpenAI prompt
system_msg = "You are a technical memoir analyst. Extract metadata coordinates from Flatline Codex Markdown notes."
user_msg = f"""Here is a Markdown file from the Codex:

{markdown}

Please extract the following 4 metadata coordinates from this content:
- Structure
- Transmission
- Purpose
- Terrain

Respond ONLY in valid JSON format like this:
{{
  "structure": "...",
  "transmission": "...",
  "purpose": "...",
  "terrain": "..."
}}"""

# 🚀 Send to OpenAI
print("🧠 Querying OpenAI (v2 API)...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]
)

reply = response.choices[0].message.content
print("\n📤 Raw OpenAI JSON:\n", reply)

# 🔍 Try to parse JSON safely
try:
    coords = json.loads(reply)
except json.JSONDecodeError:
    print("⚠️ Failed to parse JSON response:")
    print(reply)
    sys.exit(3)

# 🧱 Build YAML block and prepend to markdown
yaml_block = "---\n" + yaml.dump(coords, sort_keys=False) + "---\n\n"
final_md = yaml_block + markdown

# 💾 Save output
out_dir = "processed"
os.makedirs(out_dir, exist_ok=True)

base_name = os.path.basename(url)
json_name = base_name.replace(".md", "_coords.json")
md_name = base_name.replace(".md", "_with_coords.md")

# Save JSON
with open(os.path.join(out_dir, json_name), "w") as f:
    json.dump(coords, f, indent=2)
    print(f"✅ Saved: {json_name}")

# Save injected markdown
with open(os.path.join(out_dir, md_name), "w") as f:
    f.write(final_md)
    print(f"✅ Saved: {md_name}")
