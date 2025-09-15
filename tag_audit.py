import os
import re
import yaml
from collections import Counter
from pathlib import Path

# Configuration
VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")
TAG_PATTERN = re.compile(r"(?<!\w)#([\w/-]+)")  # Matches #tags not inside words

def extract_yaml_tags(content):
    try:
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                yaml_block = content[3:end].strip()
                parsed = yaml.safe_load(yaml_block)
                if parsed and 'tags' in parsed:
                    tags = parsed['tags']
                    if isinstance(tags, list):
                        return [str(tag) for tag in tags]
                    elif isinstance(tags, str):
                        return [tags]
    except yaml.YAMLError:
        pass
    return []

def extract_inline_tags(content):
    return TAG_PATTERN.findall(content)

def collect_tags(vault_path):
    tag_counter = Counter()
    for md_file in vault_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            yaml_tags = extract_yaml_tags(content)
            inline_tags = extract_inline_tags(content)
            all_tags = yaml_tags + inline_tags
            tag_counter.update(all_tags)
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    return tag_counter

def generate_markdown_table(counter):
    lines = ["| Tag | Count |", "|------|-------|"]
    for tag, count in counter.most_common():
        lines.append(f"| {tag} | {count} |")
    return "\n".join(lines)

def save_output(markdown_table, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_table)

if __name__ == "__main__":
    tag_counts = collect_tags(VAULT_PATH)
    md_table = generate_markdown_table(tag_counts)
    save_output(md_table, "flatline_tag_audit.md")
    print("Tag audit complete. Output saved to flatline_tag_audit.md")
