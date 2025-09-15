import os
import re
import yaml
import argparse
from pathlib import Path
from shutil import copy2

# === CONFIGURATION ===
VAULT_PATH = Path("/Users/rickshangle/Vaults/flatline-codex")
BACKUP_DIR = VAULT_PATH / ".tag_backups"
TAG_PATTERN = re.compile(r"(?<!\w)#([\w/-]+)")

def load_mapping_table(md_path):
    mapping = {}
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("| ") and not line.startswith("| Existing"):
                parts = [p.strip() for p in line.strip().split("|")[1:-1]]
                if len(parts) == 3 and parts[0] and parts[2]:
                    mapping[parts[0]] = parts[2]
    return mapping

def replace_yaml_tags(yaml_block, tag_map):
    try:
        parsed = yaml.safe_load(yaml_block)
        if parsed and isinstance(parsed, dict) and 'tags' in parsed:
            tags = parsed['tags']
            if isinstance(tags, list):
                updated = [tag_map.get(t, t) for t in tags]
                for old, new in zip(tags, updated):
                    if old != new:
                        print(f"  YAML tag was: {old}  ->  tag new: {new}")
                parsed['tags'] = sorted(set(updated))
                return yaml.dump(parsed, sort_keys=False).strip()
    except Exception:
        pass
    return None

def update_file_tags(md_path, tag_map, dry_run=False):
    original = md_path.read_text(encoding="utf-8")
    updated = original
    changed = False

    # --- YAML frontmatter ---
    if original.startswith("---"):
        end = original.find("\n---", 3)
        if end != -1:
            yaml_block = original[3:end].strip()
            fixed_yaml = replace_yaml_tags(yaml_block, tag_map)
            if fixed_yaml and fixed_yaml != yaml_block:
                updated = f"---\n{fixed_yaml}\n---" + original[end+4:]
                changed = True

    # --- Inline tags ---
    def repl(m):
        tag = m.group(1)
        new_tag = tag_map.get(tag, tag)
        if tag != new_tag:
            print(f"  inline tag was: {tag}  ->  tag new: {new_tag}")
        return f"#{new_tag}"

    new_updated = TAG_PATTERN.sub(repl, updated)
    if new_updated != updated:
        changed = True
        updated = new_updated

    if changed:
        if dry_run:
            print(f"[DRY RUN] Would update: {md_path.relative_to(VAULT_PATH)}")
        else:
            backup_path = BACKUP_DIR / md_path.relative_to(VAULT_PATH)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(md_path, backup_path)
            md_path.write_text(updated, encoding="utf-8")
            print(f"[UPDATED] {md_path.relative_to(VAULT_PATH)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rewrite tags in markdown files using a map.")
    parser.add_argument("--map", required=True, help="Path to markdown tag map table.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    args = parser.parse_args()

    tag_map = load_mapping_table(args.map)
    if not tag_map:
        print("No valid tag mappings found.")
        exit(1)

    for md_file in VAULT_PATH.rglob("*.md"):
        update_file_tags(md_file, tag_map, dry_run=args.dry_run)
