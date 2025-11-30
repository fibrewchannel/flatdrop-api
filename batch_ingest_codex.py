import os
from pathlib import Path
from ingest_github_markdown import process_markdown_file

INLOAD_DIR = Path("../flatline-codex/_inload")
PROCESSED_DIR = Path("../flatline-codex/_processed")

globals()["FLATDROP_BATCH_MODE"] = True

def batch_process():
    if not INLOAD_DIR.exists():
        print(f"❌ Missing directory: {INLOAD_DIR}")
        return

    md_files = list(INLOAD_DIR.glob("*.md"))

    if not md_files:
        print("📭 No Markdown files found in _inload/")
        return

    print(f"📦 Found {len(md_files)} files to process.")
    for file in md_files:
        print(f"\n🚀 Processing {file.name}")
        try:
            process_markdown_file(file)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__" and not globals().get("FLATDROP_BATCH_MODE"):
    # CLI mode only, prints usage
